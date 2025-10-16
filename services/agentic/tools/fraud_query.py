from typing import Any, Dict, List, Optional
from agentic.tools.base import BaseTool
from business.domain.supabase.connection import SupabaseDB
from contracts.errors import AppError
from config import get_settings
from business.model.fraud_transactions.fraud_transactions_model import FraudTransactionModel


class FraudQueryTool(BaseTool):
    """Tool for querying fraud transactions with flexible AND, OR, NOT, and comparison filters."""

    def __init__(self):
        self.db = SupabaseDB(settings_module=get_settings())
        self.table_name = "fraud_transactions"
        self._valid_columns = list(FraudTransactionModel.model_fields.keys())
        self._column_descriptions = {
            field_name: field_info.description or "No description available"
            for field_name, field_info in FraudTransactionModel.model_fields.items()
        }

    @property
    def name(self) -> str:
        return "fraud_query_tool"

    @property
    def description(self) -> str:
        col_desc_list = [
            f"- {col} ({self._column_descriptions.get(col, 'No description available')})"
            for col in self._valid_columns
        ]
        return f"""
Tool name: fraud_query_tool
Purpose: Query the 'fraud_transactions' table with flexible filters including AND, OR, NOT, and comparison operators.

Available columns:
{chr(10).join(col_desc_list)}

Arguments:
- Direct filters: Pass column=value for AND condition.
- Comparison filters: Pass column={{'gt': val, 'lt': val, 'gte': val, 'lte': val}}.
- NOT condition: Pass column={{'not': value}} to exclude a value.
- or_filters: Dictionary of columns for OR conditions (can also use comparison or NOT).
- limit: Max number of rows to return.
- offset: Starting index for pagination.

Example:
1. Simple AND:
{{'state': 'Texas', 'is_fraud': True}}

2. OR condition:
{{'state': 'Texas', 'or_filters': {{'state': 'California'}}, 'is_fraud': True}}

3. NOT condition:
{{'state': 'Texas', 'city': {{'not': 'Bogota'}}, 'is_fraud': True}}

4. Comparison filter (date or number):
{{'trans_date_trans_time': {{'gte': '2023-01-01', 'lte': '2023-12-31'}}}}

5. Full example:
{{
    'state': 'Texas',
    'or_filters': {{'state': 'California'}},
    'city': {{'not': 'Bogota'}},
    'is_fraud': True,
    'trans_date_trans_time': {{'gte': '2023-01-01'}},
    'limit': 10,
    'offset': 0
}}

Returns: List of matching transactions and total count of all matching rows.
"""

    @property
    def parameters(self) -> Dict[str, Any]:
        base_props = {
            col: {"type": "string"} if FraudTransactionModel.model_fields[col].type_ in [str, Optional[str]] else # type: ignore
                 {"type": "number"} if FraudTransactionModel.model_fields[col].type_ in [int, float, Optional[int], Optional[float]] else # type: ignore
                 {"type": "boolean"} if FraudTransactionModel.model_fields[col].type_ == bool else {"type": "string"} # type: ignore
            for col in self._valid_columns
        }

        full_props: Dict[str, Any] = dict(base_props)
        full_props["or_filters"] = {
            "type": "object",
            "properties": base_props,
            "required": []
        }

        # Add NOT and comparison support
        for col in self._valid_columns:
            full_props[col] = {
                "anyOf": [
                    base_props[col],
                    {"type": "object", "properties": {"not": base_props[col]}},
                    {"type": "object", "properties": {"gt": base_props[col], "lt": base_props[col],
                                                       "gte": base_props[col], "lte": base_props[col]}}
                ]
            }

        full_props["limit"] = {"type": "number"}
        full_props["offset"] = {"type": "number"}

        return {
            "type": "object",
            "properties": full_props,
            "required": []
        }

    def _build_filter_clause(self, filters: Dict[str, Any], valid_columns: List[str]):
        """Helper to build SQL filter strings and params."""
        clauses: List[str] = []
        params: List[Any] = []

        for key, value in filters.items():
            if key not in valid_columns:
                continue
            if isinstance(value, dict):
                # NOT
                if "not" in value:
                    clauses.append(f"{key} != %s")
                    params.append(value["not"])
                # Comparisons
                for op in ["gt", "lt", "gte", "lte"]:
                    if op in value:
                        sql_op = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<="}[op]
                        clauses.append(f"{key} {sql_op} %s")
                        params.append(value[op])
            elif isinstance(value, str):
                clauses.append(f"{key} ILIKE %s")
                params.append(value)
            else:
                clauses.append(f"{key} = %s")
                params.append(value)

        return clauses, params

    def run(self, **kwargs) -> Dict[str, Any]:
        filters: Dict[str, Any] = {k: v for k, v in kwargs.items() if k not in ["or_filters", "limit", "offset"]}
        or_filters: Dict[str, Any] = kwargs.pop("or_filters", {})
        limit: int = int(kwargs.pop("limit", 10))
        limit =  min(limit, 20)
        offset: int = int(kwargs.pop("offset", 0))

        # AND filters
        and_clauses, and_params = self._build_filter_clause(filters, self._valid_columns)
        # OR filters
        or_clauses, or_params = self._build_filter_clause(or_filters, self._valid_columns)

        where_clause = ""
        params: List[Any] = []

        if and_clauses and or_clauses:
            where_clause = f"WHERE {' AND '.join(and_clauses)} AND ({' OR '.join(or_clauses)})"
            params.extend(and_params + or_params)
        elif and_clauses:
            where_clause = f"WHERE {' AND '.join(and_clauses)}"
            params.extend(and_params)
        elif or_clauses:
            where_clause = f"WHERE {' OR '.join(or_clauses)}"
            params.extend(or_params)

        count_query = f"SELECT COUNT(*) AS total_count FROM {self.table_name} {where_clause};"
        query = f"""
            SELECT *
            FROM {self.table_name}
            {where_clause}
            ORDER BY trans_date_trans_time DESC
            LIMIT %s OFFSET %s;
        """
        params_with_limit = params + [limit, offset]

        try:
            with self.db.get_cursor() as cur:
                cur.execute(count_query, params)
                row = cur.fetchone()
                total_count = row["total_count"] if row is not None else 0 # type: ignore

                cur.execute(query, params_with_limit)
                records = cur.fetchall()

            return {"results": records, "count": total_count}

        except AppError:
            raise
        except Exception as e:
            raise AppError(
                status_code=500,
                code="fraud_query_failed",
                message=f"Unexpected error during fraud query: {str(e)}"
            )


class FraudSummaryTool(BaseTool):
    """Tool for summarizing fraud transactions and fetching distinct column values."""

    def __init__(self):
        self.db = SupabaseDB(settings_module=get_settings())
        self.table_name = "fraud_transactions"
        self._valid_columns = list(FraudTransactionModel.model_fields.keys())
        self._column_descriptions = {
            field_name: field_info.description or "No description available"
            for field_name, field_info in FraudTransactionModel.model_fields.items()
        }

    @property
    def name(self) -> str:
        return "fraud_summary_tool"

    @property
    def description(self) -> str:
        col_desc_list = [f"- {col} ({self._column_descriptions.get(col)})" for col in self._valid_columns]
        return f"""
    Tool name: fraud_summary_tool
    Purpose: Summarize fraud transaction data and fetch distinct values.

    Available columns:
    {chr(10).join(col_desc_list)}

    Arguments:
    - columns: List of columns to summarize or group by.
    - distinct: Boolean. If true, returns distinct values (max 50) per column along with total count.
    - filters: Optional AND/OR/NOT/comparison filters.
    - limit: Maximum number of rows to return.
    - order_by: Optional list of dicts with 'column' and 'order' (asc/desc).
    - time_series: Optional dict for time-based aggregation:
        - 'date_column': str
        - 'granularity': str ('day', 'month', 'year')

    Ordering rules:
    - Any column used in 'order_by' must also appear in 'columns'.
    - You can order by the automatically generated 'count' when grouping.
    - You can order by metric aliases (e.g., 'amt_sum' for SUM(amt)).
    - Use "asc" or "desc" for ascending/descending order.


    # 1. Group by city and category, sum amount, filter, order, and limit
    {{
    "columns": ["city", "category", "amt_"],
    "metrics": {{"amt": "sum"}},
    "filters": {{
        "amt": {{"gt": 100}},
        "city": {{"not": "New York"}},
        "is_fraud": true
    }},
    "order_by": [{{"column": "amt_sum", "order": "desc"}}],
    "limit": 20
    }}

    # 2. Distinct values for merchants and categories
    {{
    "columns": ["merchant", "category"],
    "distinct": true
    }}

    # 3. Time-series of monthly fraud counts for a specific city
    {{
    "time_series": {{"date_column": "trans_date_trans_time", "granularity": "month"}},
    "filters": {{"city": "Los Angeles", "is_fraud": true}}
    }}

    # 4. Group by state and gender, average transaction amount, filter by amount range
    {{
    "columns": ["state", "gender", "amt"],
    "metrics": {{"amt": "avg"}},
    "filters": {{
        "amt": {{"gte": 50, "lte": 500}},
        "is_fraud": False
    }},
    "order_by": [{{"column": "amt_avg", "order": "asc"}}],
    "limit": 15
    }}

    # 5. Time-series monthly total fraud amount for a category, filtered by job
    {{
    "columns": ["amt"],
    "metrics": {{"amt": "sum"}},
    "filters": {{
        "category": "electronics",
        "job": "Engineer",
        "is_fraud": true
    }},
    "time_series": {{"date_column": "trans_date_trans_time", "granularity": "month"}},
    "order_by": [{{"column": "amt_sum", "order": "desc"}}]
    }}
    """

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items": {"type": "string", "enum": self._valid_columns},
                    "description": "Columns to group by",
                },
                "distinct": {
                    "type": "boolean",
                    "description": "Return distinct values (max 50) per column"
                   
                },
                "metrics": {"type": "object", "description": "Optional aggregations, e.g., {'city_pop': 'sum'}"},
                "filters": {"type": "object", "description": "AND/OR/NOT/comparison filters"},
                "limit": {"type": "number", "default": 20, "description": "Max rows to return"},
                "order_by": {
                        "type": "array",
                        "description": "Optional ordering, must exist in columns",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {
                                    "type": "string",
                                    "enum": self._valid_columns,
                                    "description": "Column to order by"
                                },
                                "order": {
                                    "type": "string",
                                    "enum": ["asc", "desc"],
                                    "default": "asc",
                                    "description": "Sort direction"
                                }
                            },
                            "required": ["column"]
                        }
                    },
                "time_series": {"type": "object", "description": "Optional time series aggregation"},
            },
            "required": ["columns", "metrics"],  # <-- remove 'columns' from required
        }
        

    def _build_filter_clause(self, filters: Dict[str, Any]):
        clauses, params = [], []
        for key, value in filters.items():
            if key not in self._valid_columns:
                continue
            if isinstance(value, dict):
                if "not" in value:
                    clauses.append(f"{key} != %s")
                    params.append(value["not"])
                for op in ["gt", "lt", "gte", "lte"]:
                    if op in value:
                        sql_op = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<="}[op]
                        clauses.append(f"{key} {sql_op} %s")
                        params.append(value[op])
            elif isinstance(value, str):
                clauses.append(f"{key} ILIKE %s")
                params.append(value)
            else:
                clauses.append(f"{key} = %s")
                params.append(value)
        return clauses, params

    def run(self, **kwargs) -> Dict[str, Any]:
        columns: List[str] = kwargs.get("columns", [])
        metrics: Dict[str, str] = kwargs.get("metrics", {})
        distinct: bool = kwargs.get("distinct", False)
        filters: Dict[str, Any] = kwargs.get("filters", {})
        limit: int = int(kwargs.get("limit", 1000))
        limit = min(limit, 20)
        order_by: List[Dict[str, str]] = kwargs.get("order_by", [])
        time_series: Optional[Dict[str, str]] = kwargs.get("time_series")

        if not columns and not time_series and not distinct:
            raise AppError(status_code=400, code="missing_columns", message="Specify at least one column or time_series")

        try:
            with self.db.get_cursor() as cur:
                # WHERE clause
                where_clause, params = self._build_filter_clause(filters)
                where_clause = "WHERE " + " AND ".join(where_clause) if where_clause else ""

                # --- Time-series ---
                if time_series:
                    date_col = time_series["date_column"]
                    trunc = {"day": "DAY", "month": "MONTH", "year": "YEAR"}.get(time_series.get("granularity", "day"))
                    query = f"""
                        SELECT DATE_TRUNC('{trunc}', {date_col}) AS period, COUNT(*) AS fraud_count
                        FROM {self.table_name} {where_clause}
                        GROUP BY period
                        ORDER BY period ASC;
                    """
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return {"time_series": rows, "count": len(rows)}

                # --- Distinct ---
                if distinct:
                    cols_str = ", ".join(columns)
                    query = f"SELECT DISTINCT {cols_str} FROM {self.table_name} {where_clause} LIMIT 50;"
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    result = {col: [row[col] for row in rows] for col in columns}  # type: ignore

                    # Total distinct count
                    if len(columns) == 1:
                        count_query = f"SELECT COUNT(DISTINCT {columns[0]}) AS total_count FROM {self.table_name} {where_clause};"
                    else:
                        count_query = f"SELECT COUNT(*) AS total_count FROM (SELECT DISTINCT {cols_str} FROM {self.table_name} {where_clause}) AS sub;"
                    cur.execute(count_query, params)
                    row = cur.fetchone()
                    total_count = row["total_count"] if row else 0  # type: ignore
                    return {"distinct_values": result, "count": total_count}

                # --- Grouped summary with metrics ---
                select_parts = columns.copy()
                metric_aliases = {}
                for col, agg in metrics.items():
                    alias = f"{col}_{agg}"
                    metric_aliases[alias] = f"{agg.upper()}({col}) AS {alias}"
                    select_parts.append(metric_aliases[alias])

                group_by_cols = ", ".join(columns) if columns else ""
                select_sql = ", ".join(select_parts) if select_parts else "COUNT(*) AS count"
                query = f"SELECT {select_sql} FROM {self.table_name} {where_clause}"
                if columns:
                    query += f" GROUP BY {group_by_cols}"

                # Order by (support metrics aliases)
                if order_by:
                    order_clauses = []
                    for o in order_by:
                        col = o["column"]
                        order = o.get("order", "asc").upper()
                        if col in metric_aliases:
                            order_clauses.append(f"{col} {order}")
                        else:
                            order_clauses.append(f"{col} {order}")
                    query += f" ORDER BY {', '.join(order_clauses)}"

                query += f" LIMIT {limit};"

                cur.execute(query, params)
                rows = cur.fetchall()
                return {"summary": rows, "count": len(rows)}

        except AppError:
            raise
        except Exception as e:
            raise AppError(status_code=500, code="fraud_summary_failed", message=f"Unexpected error: {str(e)}")

