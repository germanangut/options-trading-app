from __future__ import annotations

from pathlib import Path
import sqlite3

from backend.contracts.ticket_models import ExecutionTicket
from backend.repositories.ticket_repository import TicketRepository


class SQLiteTicketRepository(TicketRepository):
    """SQLite-backed persistence for user-owned execution preparation tickets."""

    def __init__(self, database_path: str | Path):
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_ticket (
                    ticket_id                   TEXT PRIMARY KEY,
                    owner_user_id               TEXT NOT NULL,
                    trade_id                    TEXT NOT NULL,
                    source_scan_id              TEXT,
                    ticker                      TEXT NOT NULL,
                    strategy_key                TEXT NOT NULL,
                    strategy_label              TEXT NOT NULL,
                    directional_bias            TEXT,
                    expiration_date             TEXT,
                    short_strike                REAL,
                    long_strike                 REAL,
                    underlying_price_at_creation REAL,
                    net_credit_estimate         REAL,
                    max_risk_estimate           REAL,
                    adjusted_score_at_creation  REAL,
                    quantity                    INTEGER NOT NULL DEFAULT 1,
                    order_intent                TEXT NOT NULL DEFAULT 'open_credit',
                    execution_status            TEXT NOT NULL DEFAULT 'draft',
                    note                        TEXT,
                    created_at                  TEXT NOT NULL,
                    updated_at                  TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ticket_owner_updated
                ON execution_ticket (owner_user_id, updated_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ticket_owner_trade
                ON execution_ticket (owner_user_id, trade_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ticket_owner_status
                ON execution_ticket (owner_user_id, execution_status)
                """
            )

    def _row_to_ticket(self, row: sqlite3.Row | None) -> ExecutionTicket | None:
        if row is None:
            return None
        return ExecutionTicket(
            ticket_id=row["ticket_id"],
            owner_user_id=row["owner_user_id"],
            trade_id=row["trade_id"],
            source_scan_id=row["source_scan_id"],
            ticker=row["ticker"],
            strategy_key=row["strategy_key"],
            strategy_label=row["strategy_label"],
            directional_bias=row["directional_bias"],
            expiration_date=row["expiration_date"],
            short_strike=row["short_strike"],
            long_strike=row["long_strike"],
            underlying_price_at_creation=row["underlying_price_at_creation"],
            net_credit_estimate=row["net_credit_estimate"],
            max_risk_estimate=row["max_risk_estimate"],
            adjusted_score_at_creation=row["adjusted_score_at_creation"],
            quantity=row["quantity"],
            order_intent=row["order_intent"],
            execution_status=row["execution_status"],
            note=row["note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_ticket(self, ticket: ExecutionTicket) -> ExecutionTicket:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO execution_ticket (
                    ticket_id, owner_user_id, trade_id, source_scan_id,
                    ticker, strategy_key, strategy_label, directional_bias,
                    expiration_date, short_strike, long_strike,
                    underlying_price_at_creation, net_credit_estimate,
                    max_risk_estimate, adjusted_score_at_creation,
                    quantity, order_intent, execution_status, note,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    ticket.ticket_id,
                    ticket.owner_user_id,
                    ticket.trade_id,
                    ticket.source_scan_id,
                    ticket.ticker,
                    ticket.strategy_key,
                    ticket.strategy_label,
                    ticket.directional_bias,
                    ticket.expiration_date,
                    ticket.short_strike,
                    ticket.long_strike,
                    ticket.underlying_price_at_creation,
                    ticket.net_credit_estimate,
                    ticket.max_risk_estimate,
                    ticket.adjusted_score_at_creation,
                    ticket.quantity,
                    ticket.order_intent,
                    ticket.execution_status,
                    ticket.note,
                    ticket.created_at,
                    ticket.updated_at,
                ),
            )
        stored = self.get_ticket(ticket.ticket_id, user_id=ticket.owner_user_id)
        if stored is None:
            raise RuntimeError("Execution ticket was not persisted.")
        return stored

    def get_ticket(self, ticket_id: str, *, user_id: str) -> ExecutionTicket | None:
        if not ticket_id or not user_id:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM execution_ticket WHERE ticket_id = ? AND owner_user_id = ?",
                (ticket_id, user_id),
            ).fetchone()
        return self._row_to_ticket(row)

    def get_tickets_by_trade(
        self,
        trade_id: str,
        *,
        user_id: str,
    ) -> list[ExecutionTicket]:
        if not trade_id or not user_id:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM execution_ticket
                WHERE owner_user_id = ? AND trade_id = ?
                ORDER BY updated_at DESC, ticket_id DESC
                """,
                (user_id, trade_id),
            ).fetchall()
        return [t for row in rows if (t := self._row_to_ticket(row)) is not None]

    def list_tickets(
        self,
        *,
        user_id: str,
        execution_status: str | None = None,
        limit: int | None = None,
    ) -> list[ExecutionTicket]:
        if not user_id:
            return []

        query = "SELECT * FROM execution_ticket WHERE owner_user_id = ?"
        params: list[object] = [user_id]

        if execution_status:
            query = f"{query} AND execution_status = ?"
            params.append(execution_status)

        query = f"{query} ORDER BY updated_at DESC, ticket_id DESC"
        if isinstance(limit, int) and limit > 0:
            query = f"{query} LIMIT ?"
            params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [t for row in rows if (t := self._row_to_ticket(row)) is not None]

    def update_ticket(
        self,
        ticket_id: str,
        *,
        user_id: str,
        quantity: int | None,
        note: str | None,
        clear_note: bool,
        execution_status: str | None,
        updated_at: str,
    ) -> ExecutionTicket | None:
        if not ticket_id or not user_id:
            return None

        existing = self.get_ticket(ticket_id, user_id=user_id)
        if existing is None:
            return None

        new_quantity = quantity if quantity is not None else existing.quantity
        new_note = None if clear_note else (note if note is not None else existing.note)
        new_status = execution_status if execution_status is not None else existing.execution_status

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE execution_ticket
                SET quantity = ?, note = ?, execution_status = ?, updated_at = ?
                WHERE ticket_id = ? AND owner_user_id = ?
                """,
                (new_quantity, new_note, new_status, updated_at, ticket_id, user_id),
            )

        return self.get_ticket(ticket_id, user_id=user_id)

    def clear(self, *, user_id: str | None = None) -> None:
        with self._connect() as connection:
            if user_id is None:
                connection.execute("DELETE FROM execution_ticket")
            else:
                connection.execute(
                    "DELETE FROM execution_ticket WHERE owner_user_id = ?",
                    (user_id,),
                )
