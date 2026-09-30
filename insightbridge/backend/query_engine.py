"""Map structured business intents to safe, fixed SQL templates."""

from dataclasses import dataclass

from db import execute_read_query


SEMANTIC_SCHEMA = {
    "companies": {"table": "table1", "name": "field1", "state": "field7", "status": "field10"},
    "plans": {"table": "table4", "name": "field1", "tier": "field2", "billing_cycle": "field3"},
    "subscriptions": {"table": "table6", "company_id": "ref1", "plan_id": "ref2", "status": "field1", "mrr": "field6"},
    "transactions": {"table": "table7", "company_id": "ref2", "amount": "field4", "status": "field8", "quarter": "field10", "year": "field11"},
    "opportunities": {"table": "table8", "company_id": "ref1", "name": "field1", "stage": "field2", "revenue": "field4"},
    "campaigns": {"table": "table9", "name": "field1", "spend": "field7", "conversions": "field10", "leads": "field11"},
    "health": {"table": "table12", "company_id": "ref1", "score": "field1", "churn_risk": "field2"},
}


@dataclass
class QueryDefinition:
    sql: str
    parameters: tuple
    tables: list[str]
    filters: list[str]


def build_query(parsed: dict) -> QueryDefinition:
    intent = parsed["intent"]

    if intent == "customers_by_plan_location":
        clauses = ["s.field1 IN ('active', 'trial')"]
        parameters = []
        filters = ["Subscription status = active or trial"]
        if parsed.get("state"):
            clauses.append("c.field7 = ?")
            parameters.append(parsed["state"])
            filters.append(f"State = {parsed['state']}")
        if parsed.get("plan_tier"):
            clauses.append("p.field2 = ?")
            parameters.append(parsed["plan_tier"])
            filters.append(f"Plan tier = {parsed['plan_tier']}")
        sql = f"""SELECT c.field1 AS Company, p.field1 AS Plan, p.field2 AS Tier,
       c.field7 AS State, s.field6 AS MRR
FROM table1 c
JOIN table6 s ON s.ref1 = c.id
JOIN table4 p ON p.id = s.ref2
WHERE {' AND '.join(clauses)}
ORDER BY c.field1
LIMIT 100"""
        return QueryDefinition(sql, tuple(parameters), ["Companies", "Subscriptions", "Pricing Plans"], filters)

    if intent == "revenue_by_quarter":
        year = parsed.get("year")
        clauses = ["field8 = 'completed'"]
        parameters = []
        filters = ["Payment status = completed"]
        if year:
            clauses.append("field11 = ?")
            parameters.append(year)
            filters.append(f"Fiscal year = {year}")
        sql = f"""SELECT field11 AS Year, field10 AS Quarter,
       ROUND(SUM(field4), 2) AS Revenue
FROM table7
WHERE {' AND '.join(clauses)}
GROUP BY field11, field10
ORDER BY field11, CASE field10 WHEN 'Q1' THEN 1 WHEN 'Q2' THEN 2 WHEN 'Q3' THEN 3 ELSE 4 END
LIMIT 100"""
        return QueryDefinition(sql, tuple(parameters), ["Transactions"], filters)

    if intent == "customer_health":
        risks = parsed.get("churn_risks") or []
        clauses, parameters, filters = [], [], []
        if risks:
            clauses.append(f"h.field2 IN ({','.join('?' for _ in risks)})")
            parameters.extend(risks)
            filters.append(f"Churn risk = {' or '.join(risks)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""SELECT c.field1 AS Company, h.field1 AS Health_Score,
       h.field2 AS Churn_Risk, h.field7 AS Renewal_Probability,
       h.field4 AS Support_Tickets
FROM table12 h
JOIN table1 c ON c.id = h.ref1
{where}
ORDER BY CASE h.field2 WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
         h.field1
LIMIT 100"""
        return QueryDefinition(sql, tuple(parameters), ["Customer Health", "Companies"], filters)

    if intent == "sales_pipeline":
        clauses, parameters, filters = [], [], []
        if parsed.get("stage"):
            clauses.append("o.field2 = ?")
            parameters.append(parsed["stage"])
            filters.append(f"Sales stage = {parsed['stage']}")
        elif parsed.get("open_only"):
            clauses.append("o.field2 NOT IN ('closed_won', 'closed_lost')")
            filters.append("Sales stage = open")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""SELECT o.field1 AS Opportunity, c.field1 AS Company,
       o.field2 AS Stage, o.field4 AS Expected_Revenue,
       o.field5 AS Probability, o.field6 AS Expected_Close_Date
FROM table8 o
JOIN table1 c ON c.id = o.ref1
{where}
ORDER BY o.field4 DESC
LIMIT 100"""
        return QueryDefinition(sql, tuple(parameters), ["Sales Opportunities", "Companies"], filters)

    if intent == "subscriptions_by_plan":
        sql = """SELECT p.field1 AS Plan, p.field2 AS Tier,
       COUNT(s.id) AS Subscriptions, ROUND(SUM(s.field6), 2) AS Total_MRR
FROM table4 p
LEFT JOIN table6 s ON s.ref2 = p.id
GROUP BY p.id, p.field1, p.field2
ORDER BY Subscriptions DESC, p.field1
LIMIT 100"""
        return QueryDefinition(sql, (), ["Pricing Plans", "Subscriptions"], [])

    if intent == "top_customers":
        sql = """SELECT c.field1 AS Company, ROUND(SUM(t.field4), 2) AS Revenue
FROM table7 t
JOIN table1 c ON c.id = t.ref2
WHERE t.field8 = 'completed'
GROUP BY c.id, c.field1
ORDER BY Revenue DESC
LIMIT 10"""
        return QueryDefinition(sql, (), ["Transactions", "Companies"], ["Payment status = completed", "Top 10"])

    if intent == "marketing_performance":
        sql = """SELECT field1 AS Campaign, field2 AS Type, field7 AS Spend,
       field10 AS Conversions, field11 AS Leads,
       ROUND(CASE WHEN field10 > 0 THEN field7 / field10 END, 2) AS Cost_Per_Conversion
FROM table9
ORDER BY Conversions DESC
LIMIT 100"""
        return QueryDefinition(sql, (), ["Marketing Campaigns"], [])

    raise ValueError("Unsupported intent")


def answer_question(parsed: dict) -> dict:
    definition = build_query(parsed)
    columns, rows = execute_read_query(definition.sql, definition.parameters)
    intent = parsed["intent"]

    if not rows:
        summary = "No matching data was found."
    elif intent == "revenue_by_quarter":
        total = sum(float(row[2]) for row in rows)
        summary = f"Revenue across {len(rows)} quarter(s) was ${total:,.2f}."
    elif intent == "sales_pipeline":
        total = sum(float(row[3] or 0) for row in rows)
        summary = f"Found {len(rows)} opportunities worth ${total:,.2f} in expected revenue."
    else:
        summary = f"Found {len(rows)} matching result{'s' if len(rows) != 1 else ''}."

    return {
        "summary": summary,
        "columns": columns,
        "rows": rows,
        "sql": definition.sql,
        "explanation": {
            "intent": intent,
            "tables": definition.tables,
            "filters": definition.filters,
            "parser": parsed.get("parser", "rules"),
        },
        "clarification": None,
    }
