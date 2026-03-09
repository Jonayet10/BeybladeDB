from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
from mysql.connector import Error as MySQLError

from api.db import get_conn
from api.schemas import (
    LoginRequest,
    AddToCollectionRequest,
    DeleteFromCollectionRequest,
    UpdateCollectionConditionRequest,
)

app = FastAPI(title="BeybladeDB API")

app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def root():
    return FileResponse("web/login.html")


@app.get("/login")
def login_page():
    return FileResponse("web/login.html")


@app.get("/beyblades-page")
def beyblades_page():
    return FileResponse("web/beyblades.html")


@app.get("/battles-page")
def battles_page():
    return FileResponse("web/battles.html")


def _table_columns(table: str) -> list[str]:
    """
    Query INFORMATION_SCHEMA to retrieve the ordered list of column names
    for a given table in the current database.
    """

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION;
            """,
            (table,),
        )
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def _pick_col(cols: list[str], candidates: list[str]) -> Optional[str]:
    """
    Return the first column name from `candidates` that exists in `cols`.
    Used to support schemas where column naming conventions differ.
    """

    s = set(cols)
    for c in candidates:
        if c in s:
            return c
    return None


@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT authenticate(%s, %s);", (req.username.lower(), req.password))
        ok = cur.fetchone()
        if not ok or ok[0] != 1:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        cur.execute("SELECT is_admin FROM users WHERE username = %s;", (req.username.lower(),))
        row = cur.fetchone()
        is_admin = bool(row[0]) if row else False
        return {"ok": True, "username": req.username.lower(), "is_admin": is_admin}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/beyblades")
def get_beyblades(
    type: Optional[str] = Query(default=None),
    series: Optional[str] = Query(default=None),
):
    """
    Return a list of beyblades from the database, optionally filtered by
    type or series.

    Response format:
    {
        "items": [ {beyblade row}, {beyblade row}, ... ]
    }
    """

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        q = "SELECT * FROM beyblades"
        params = []
        where = []

        if type:
          where.append("type = %s")
          params.append(type)

        if series:
          where.append("series LIKE %s")
          params.append(f"%{series}%")

        if where:
            q += " WHERE " + " AND ".join(where)

        q += " ORDER BY name;"
        cur.execute(q, tuple(params))
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/users/{username}/collection")
def get_collection(username: str):
    """
    Return the beyblade collection belonging to a user.

    Response format:
    {
        "items": [ {collection entry}, ... ]
    }
    """
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        q = """
        SELECT ub.user_beyblade_ID, b.beyblade_ID, b.name, b.type, b.series, b.is_custom, ub.bey_condition
        FROM beyblades b
        JOIN beycollection ub ON b.beyblade_ID = ub.beyblade_ID
        JOIN users u ON ub.user_ID = u.user_ID
        WHERE u.username = %s
        ORDER BY b.name;
        """
        cur.execute(q, (username.lower(),))
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/api/collection/add")
def add_to_collection_alias(req: AddToCollectionRequest):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_ID FROM users WHERE username = %s;", (req.username.lower(),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = int(row[0])

        cur.execute(
            "INSERT INTO beycollection (user_ID, beyblade_ID, bey_condition) VALUES (%s, %s, %s);",
            (user_id, req.beyblade_id, req.bey_condition),
        )
        conn.commit()
        return {"ok": True}
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.delete("/api/users/{username}/collection/{user_beyblade_id}")
def delete_from_collection(username: str, user_beyblade_id: int):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_ID FROM users WHERE username = %s;", (username.lower(),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = int(row[0])

        # Detect the actual battle table column names dynamically so the API works
        # even if the database schema uses slightly different naming conventions.
        battle_cols = _table_columns("battles")
        p1 = _pick_col(battle_cols, ["player1_beyblade_ID", "player1_ID", "player1_beyblade_id", "player1"])
        p2 = _pick_col(battle_cols, ["player2_beyblade_ID", "player2_ID", "player2_beyblade_id", "player2"])
        w = _pick_col(battle_cols, ["winner_ID", "winner_id", "winner"])

        # Prevent deleting a collection item if it is still referenced by battles.
        # This protects referential integrity at the application level.
        if p1 or p2 or w:
            checks = []
            params = []

            if p1:
                checks.append(f"{p1} = %s")
                params.append(user_beyblade_id)
            if p2:
                checks.append(f"{p2} = %s")
                params.append(user_beyblade_id)
            if w:
                checks.append(f"{w} = %s")
                params.append(user_beyblade_id)

            if checks:
                cur.execute(
                    f"SELECT COUNT(*) FROM battles WHERE {' OR '.join(checks)};",
                    tuple(params),
                )
                cnt = cur.fetchone()[0]
                if cnt and int(cnt) > 0:
                    raise HTTPException(
                        status_code=409,
                        detail="Cannot delete: this collection item is referenced by battles. Remove/adjust those battles first.",
                    )

        cur.execute(
            "DELETE FROM beycollection WHERE user_beyblade_ID = %s AND user_ID = %s;",
            (user_beyblade_id, user_id),
        )

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Collection item not found")

        conn.commit()
        return {"ok": True}
    except HTTPException:
        conn.rollback()
        raise
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/api/collection/delete")
def delete_from_collection_alias(req: DeleteFromCollectionRequest):
    return delete_from_collection(req.username, req.user_beyblade_id)


@app.get("/api/leaderboard")
def leaderboard():
    """
    Return a leaderboard of beyblades ranked by total battle wins.

    Response format:
    {
        "items": [ {leaderboard row}, ... ]
    }
    """

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        q = """
        SELECT bb.beyblade_ID, bb.name, bb.type, COUNT(*) as wins
        FROM battles b
        INNER JOIN beycollection ub ON b.winner_ID = ub.user_beyblade_ID
        INNER JOIN beyblades bb ON ub.beyblade_ID = bb.beyblade_ID
        GROUP BY bb.beyblade_ID, bb.name, bb.type
        ORDER BY wins DESC, bb.name;
        """
        cur.execute(q)
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/parts")
def get_parts(
    part_type: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
):
    """
    Return a list of parts, optionally filtered by part type or search text.

    Response format:
    {
        "items": [ {part row}, ... ]
    }
    """

    # Detect column names dynamically to support small schema differences
    # (e.g., part_ID vs part_id).
    cols = _table_columns("parts")
    name_col = _pick_col(cols, ["name", "part_name", "partName", "part"])
    desc_col = _pick_col(cols, ["description", "part_description", "descr", "desc"])
    type_col = _pick_col(cols, ["part_type", "type"])
    id_col = _pick_col(cols, ["part_ID", "part_id", "id"])

    if not id_col:
        raise HTTPException(status_code=500, detail="Could not detect parts primary key column.")

    order_col = name_col or id_col

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM parts"
        params = []
        where = []

        if part_type and type_col:
            where.append(f"{type_col} = %s")
            params.append(part_type)

        if q:
            like = f"%{q}%"
            ors = []
            if name_col:
                ors.append(f"{name_col} LIKE %s")
                params.append(like)
            if desc_col:
                ors.append(f"{desc_col} LIKE %s")
                params.append(like)
            if ors:
                where.append("(" + " OR ".join(ors) + ")")

        if where:
            sql += " WHERE " + " AND ".join(where)

        if type_col:
            sql += f" ORDER BY {type_col}, {order_col};"
        else:
            sql += f" ORDER BY {order_col};"

        cur.execute(sql, tuple(params))
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/beyblades/{beyblade_id}/parts")
def get_beyblade_parts(beyblade_id: str):
    """
    Return detailed information for a beyblade including its associated parts.

    Response format:
    {
        "item": {beyblade + part information}
    }
    """

    pcols = _table_columns("parts")
    pname = _pick_col(pcols, ["name", "part_name", "partName"])
    pweight = _pick_col(pcols, ["weight", "part_weight", "grams", "weight_g"])
    pdesc = _pick_col(pcols, ["description", "part_description", "descr", "desc"])
    pid = _pick_col(pcols, ["part_ID", "part_id", "id"])

    if not pid:
        raise HTTPException(status_code=500, detail="Could not detect parts primary key column.")

    def sel(alias: str, prefix: str) -> str:
        # Helper to dynamically build SELECT fields for each part component.
        fields = [f"{alias}.{pid} AS {prefix}_id"]
        if pname:
            fields.append(f"{alias}.{pname} AS {prefix}_name")
        if pweight:
            fields.append(f"{alias}.{pweight} AS {prefix}_weight")
        if pdesc:
            fields.append(f"{alias}.{pdesc} AS {prefix}_description")
        return ",\n          ".join(fields)

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        sql = f"""
        SELECT
          b.beyblade_ID,
          b.name AS beyblade_name,
          b.type AS beyblade_type,
          b.series AS beyblade_series,

          b.face_bolt_id,
          {sel("fb", "face_bolt")},

          b.energy_ring_id,
          {sel("er", "energy_ring")},

          b.fusion_wheel_id,
          {sel("fw", "fusion_wheel")},

          b.spin_track_id,
          {sel("st", "spin_track")},

          b.performance_tip_id,
          {sel("pt", "performance_tip")}

        FROM beyblades b
        LEFT JOIN parts fb ON fb.{pid} = b.face_bolt_id
        LEFT JOIN parts er ON er.{pid} = b.energy_ring_id
        LEFT JOIN parts fw ON fw.{pid} = b.fusion_wheel_id
        LEFT JOIN parts st ON st.{pid} = b.spin_track_id
        LEFT JOIN parts pt ON pt.{pid} = b.performance_tip_id
        WHERE b.beyblade_ID = %s;
        """
        cur.execute(sql, (beyblade_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Beyblade not found")
        return {"item": row}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/parts/{part_id}")
def get_part(part_id: str):
    """
    Return a single part by its ID.

    Response format:
    {
        "item": {part row}
    }
    """

    cols = _table_columns("parts")
    id_col = _pick_col(cols, ["part_ID", "part_id", "id"])

    if not id_col:
        raise HTTPException(status_code=500, detail="Could not detect parts primary key column.")

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT * FROM parts WHERE {id_col} = %s;", (part_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Part not found")
        return {"item": row}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/beyblades/heaviest")
def heaviest_beyblade_for_type(type: str = Query(...)):
    """
    Return the heaviest beyblade of the requested type.

    Response format:
    {
        "item": {beyblade row with total_weight}
    }
    """

    cols = _table_columns("parts")
    pid = _pick_col(cols, ["part_ID", "part_id", "id"])
    pweight = _pick_col(cols, ["weight", "part_weight", "grams", "weight_g"])

    if not pid or not pweight:
        raise HTTPException(status_code=500, detail="Could not detect parts columns needed for weight.")

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        sql = f"""
        SELECT
          b.beyblade_ID,
          b.name,
          b.type,
          b.series,
          (
            COALESCE(fb.{pweight}, 0) +
            COALESCE(er.{pweight}, 0) +
            COALESCE(fw.{pweight}, 0) +
            COALESCE(st.{pweight}, 0) +
            COALESCE(pt.{pweight}, 0)
          ) AS total_weight
        FROM beyblades b
        LEFT JOIN parts fb ON fb.{pid} = b.face_bolt_id
        LEFT JOIN parts er ON er.{pid} = b.energy_ring_id
        LEFT JOIN parts fw ON fw.{pid} = b.fusion_wheel_id
        LEFT JOIN parts st ON st.{pid} = b.spin_track_id
        LEFT JOIN parts pt ON pt.{pid} = b.performance_tip_id
        WHERE b.type = %s
        ORDER BY total_weight DESC, b.name
        LIMIT 1;
        """
        cur.execute(sql, (type,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No beyblades found for that type")
        return {"item": row}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/tournaments")
def get_tournaments():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT DISTINCT tournament_name FROM battles ORDER BY tournament_name;")
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/battles/locations")
def get_battle_locations():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT DISTINCT location FROM battles ORDER BY location;")
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/tournaments/{tournament_name}/results")
def get_tournament_results(tournament_name: str):
    """
    Return the battle results for a given tournament, including winner and loser
    beyblade names when available.

    Response format:
    {
        "items": [ {tournament result row}, ... ]
    }
    """

    # Detect battles table column names dynamically to handle schema variations.
    bcols = _table_columns("battles")

    battle_id = _pick_col(bcols, ["battle_ID", "battle_id", "id"])
    tcol = _pick_col(bcols, ["tournament_name", "tournament"])
    lcol = _pick_col(bcols, ["location", "battle_location"])
    p1 = _pick_col(bcols, ["player1_beyblade_ID", "player1_ID", "player1_beyblade_id", "player1"])
    p2 = _pick_col(bcols, ["player2_beyblade_ID", "player2_ID", "player2_beyblade_id", "player2"])
    w = _pick_col(bcols, ["winner_ID", "winner_id", "winner"])

    if not tcol or not p1 or not p2 or not w:
        raise HTTPException(status_code=500, detail="Could not detect battles columns needed for tournament results.")

    b_id_expr = f"b.{battle_id} AS battle_ID" if battle_id else "NULL AS battle_ID"
    loc_expr = f"b.{lcol} AS location" if lcol else "NULL AS location"

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        sql = f"""
        SELECT
          {b_id_expr},
          b.{tcol} AS tournament_name,
          {loc_expr},
          b.{w} AS winner_ID,
          CASE WHEN b.{w} = b.{p1} THEN b.{p2} ELSE b.{p1} END AS loser_ID,
          wbb.name AS winner_beyblade_name,
          lbb.name AS loser_beyblade_name
        FROM battles b
        LEFT JOIN beycollection wbc ON wbc.user_beyblade_ID = b.{w}
        LEFT JOIN beyblades wbb ON wbb.beyblade_ID = wbc.beyblade_ID
        LEFT JOIN beycollection lbc ON lbc.user_beyblade_ID = (CASE WHEN b.{w} = b.{p1} THEN b.{p2} ELSE b.{p1} END)
        LEFT JOIN beyblades lbb ON lbb.beyblade_ID = lbc.beyblade_ID
        WHERE b.{tcol} = %s
        ORDER BY {("b." + battle_id) if battle_id else "b." + tcol};
        """
        cur.execute(sql, (tournament_name,))
        return {"items": cur.fetchall()}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/api/tournaments/by-location")
def get_tournaments_by_location(location: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT DISTINCT tournament_name
            FROM battles
            WHERE location = %s
            ORDER BY tournament_name;
            """,
            (location,),
        )
        return {"items": cur.fetchall()}
    finally:
        cur.close()
        conn.close()

@app.patch("/api/users/{username}/collection/{user_beyblade_id}")
def update_collection_condition(username: str, user_beyblade_id: int, req: UpdateCollectionConditionRequest):
    """
    Update the condition of a beyblade in a user's collection.

    Response format:
    {
        "ok": True
    }
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        if username.lower() != req.username.lower():
            raise HTTPException(status_code=400, detail="Username mismatch")

        cur.execute("SELECT user_ID FROM users WHERE username = %s;", (username.lower(),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = int(row[0])

        cur.execute(
            """
            UPDATE beycollection
            SET bey_condition = %s
            WHERE user_beyblade_ID = %s AND user_ID = %s;
            """,
            (req.bey_condition, user_beyblade_id, user_id),
        )

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Collection item not found")

        conn.commit()
        return {"ok": True}
    except HTTPException:
        conn.rollback()
        raise
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()