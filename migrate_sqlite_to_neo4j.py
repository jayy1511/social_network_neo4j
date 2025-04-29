import sqlite3
from neo4j import GraphDatabase

# === CONFIG ===
SQLITE_DB = 'social_network.db'
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "admin123"

# === Connect to SQLite ===
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cursor = sqlite_conn.cursor()

# === Connect to Neo4j ===
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def migrate_users():
    users = sqlite_cursor.execute("SELECT id, username, name FROM users").fetchall()
    with neo4j_driver.session() as session:
        for user_id, username, name in users:
            session.run(
                "MERGE (u:User {old_id: $user_id}) "
                "SET u.username = $username, u.name = $name",
                user_id=user_id, username=username, name=name
            )
    print(f"✅ Migrated {len(users)} users.")

def migrate_posts():
    posts = sqlite_cursor.execute("SELECT id, user_id, content, timestamp FROM posts").fetchall()
    with neo4j_driver.session() as session:
        for post_id, user_id, content, timestamp in posts:
            session.run(
                """
                MATCH (u:User {old_id: $user_id})
                CREATE (p:Post {content: $content, timestamp: datetime($timestamp)})
                MERGE (u)-[:POSTED]->(p)
                """,
                user_id=user_id, content=content, timestamp=timestamp
            )
    print(f"✅ Migrated {len(posts)} posts.")

def migrate_followers():
    links = sqlite_cursor.execute("SELECT follower_id, followee_id FROM followers").fetchall()
    with neo4j_driver.session() as session:
        for follower_id, followee_id in links:
            session.run(
                """
                MATCH (a:User {old_id: $follower_id})
                MATCH (b:User {old_id: $followee_id})
                MERGE (a)-[:FOLLOWS]->(b)
                """,
                follower_id=follower_id, followee_id=followee_id
            )
    print(f"✅ Migrated {len(links)} follow relationships.")

def clear_temp_ids():
    # Optional cleanup if you don’t want to keep old_id
    with neo4j_driver.session() as session:
        session.run("MATCH (u:User) REMOVE u.old_id")

if __name__ == "__main__":
    print("🚀 Starting migration...")
    migrate_users()
    migrate_posts()
    migrate_followers()
    # clear_temp_ids()  # Uncomment if you want to remove old_id field
    neo4j_driver.close()
    sqlite_conn.close()
    print("🎉 Migration complete.")
