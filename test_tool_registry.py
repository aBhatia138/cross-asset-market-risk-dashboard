from src.tool_registry import execute_tool

#Test 1: Unknown tool
result = execute_tool(
    "delete_database",
    {}
)

print("\nTEST 1: Unknown tool")
print(result)

#Test 2: Unknown asset RIC
result = execute_tool(
    "get_asset_snapshot",
    {"ric":"INVALID"}
)

print("\nTEST 2: Unsupported RIC")
print(result)

#Test 3: Missing argument 
result = execute_tool(
    "get_asset_snapshot",
    {}
)

print("\nTEST 3: Missing Argument")
print(result)
