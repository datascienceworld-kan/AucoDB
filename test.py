from aucodb.database import AucoDB, Collection, Record

new_db = AucoDB(data_path="agent_template/agent_template.json")
print("\nLoaded database from JSON:")
for record in new_db.collections["agents"].records:
    print(type(record), record)
    for tool in record.tools:
        print(tool)
