from foundational_config import query_proprietary_data

print(query_proprietary_data("List all forwarders with CIF terms", "companies"))
print(query_proprietary_data("Average surcharge where validity_days > 15", "quotes"))
