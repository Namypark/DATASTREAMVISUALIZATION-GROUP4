from src.data_collection.data_collection_agent import get_connection, fetch_all


def main():
    print("Hello from data!")


if __name__ == "__main__":
    # Example usage
    # Example: read the first five rows from the newly created students table.
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM robot_readings LIMIT 5;")
            records = cursor.fetchall()

            for record in records:
                print(record)

    readings_df = fetch_all()

    print(readings_df)
    print(readings_df.head(5))
