import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import SessionLocal, create_tables
from models.user import User
from models.author import Author
from models.genre import Genre
from models.book import Book
from utils.security import hash_password


async def seed_admin(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == "admin"))
    existing = result.scalars().first()
    if existing is not None:
        print("Admin user already exists, skipping.")
        return existing

    admin = User(
        display_name="Admin",
        email="admin@booknest.com",
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)
    await db.flush()
    await db.refresh(admin)
    print("Created admin user (username: admin, password: admin123).")
    return admin


async def seed_customer(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == "customer"))
    existing = result.scalars().first()
    if existing is not None:
        print("Customer user already exists, skipping.")
        return existing

    customer = User(
        display_name="Jane Reader",
        email="jane@example.com",
        username="customer",
        password_hash=hash_password("customer123"),
        role="customer",
    )
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    print("Created customer user (username: customer, password: customer123).")
    return customer


async def seed_genres(db: AsyncSession) -> list[Genre]:
    genre_names = [
        "Fiction",
        "Non-Fiction",
        "Science Fiction",
        "Fantasy",
        "Mystery",
        "Romance",
        "Thriller",
        "Biography",
        "History",
        "Self-Help",
    ]

    genres: list[Genre] = []
    for name in genre_names:
        result = await db.execute(select(Genre).where(Genre.name == name))
        existing = result.scalars().first()
        if existing is not None:
            genres.append(existing)
        else:
            genre = Genre(name=name)
            db.add(genre)
            await db.flush()
            await db.refresh(genre)
            genres.append(genre)
            print(f"Created genre: {name}")

    return genres


async def seed_authors(db: AsyncSession) -> list[Author]:
    author_data = [
        {"name": "F. Scott Fitzgerald", "bio": "American novelist and short story writer."},
        {"name": "George Orwell", "bio": "English novelist, essayist, and critic."},
        {"name": "J.K. Rowling", "bio": "British author best known for the Harry Potter series."},
        {"name": "Isaac Asimov", "bio": "American writer and professor of biochemistry."},
        {"name": "Agatha Christie", "bio": "English writer known for detective novels."},
    ]

    authors: list[Author] = []
    for data in author_data:
        result = await db.execute(select(Author).where(Author.name == data["name"]))
        existing = result.scalars().first()
        if existing is not None:
            authors.append(existing)
        else:
            author = Author(name=data["name"], bio=data["bio"])
            db.add(author)
            await db.flush()
            await db.refresh(author)
            authors.append(author)
            print(f"Created author: {data['name']}")

    return authors


async def seed_books(db: AsyncSession, authors: list[Author], genres: list[Genre]) -> list[Book]:
    books_data = [
        {
            "title": "The Great Gatsby",
            "isbn": "978-0-7432-7356-5",
            "price": 12.99,
            "stock": 25,
            "description": "A novel set in the Roaring Twenties that explores themes of wealth, class, and the American Dream.",
            "publication_year": 1925,
            "pages": 180,
            "author_index": 0,
            "genre_index": 0,
        },
        {
            "title": "1984",
            "isbn": "978-0-451-52493-5",
            "price": 14.99,
            "stock": 30,
            "description": "A dystopian novel set in a totalitarian society ruled by Big Brother.",
            "publication_year": 1949,
            "pages": 328,
            "author_index": 1,
            "genre_index": 2,
        },
        {
            "title": "Animal Farm",
            "isbn": "978-0-451-52634-2",
            "price": 9.99,
            "stock": 40,
            "description": "An allegorical novella reflecting events leading up to the Russian Revolution.",
            "publication_year": 1945,
            "pages": 112,
            "author_index": 1,
            "genre_index": 0,
        },
        {
            "title": "Harry Potter and the Philosopher's Stone",
            "isbn": "978-0-7475-3269-9",
            "price": 19.99,
            "stock": 50,
            "description": "The first novel in the Harry Potter series, following a young wizard's journey.",
            "publication_year": 1997,
            "pages": 223,
            "author_index": 2,
            "genre_index": 3,
        },
        {
            "title": "Harry Potter and the Chamber of Secrets",
            "isbn": "978-0-7475-3849-3",
            "price": 19.99,
            "stock": 45,
            "description": "The second installment in the Harry Potter series.",
            "publication_year": 1998,
            "pages": 251,
            "author_index": 2,
            "genre_index": 3,
        },
        {
            "title": "Foundation",
            "isbn": "978-0-553-29335-7",
            "price": 15.99,
            "stock": 20,
            "description": "The first novel in Asimov's Foundation series about the fall of a Galactic Empire.",
            "publication_year": 1951,
            "pages": 244,
            "author_index": 3,
            "genre_index": 2,
        },
        {
            "title": "I, Robot",
            "isbn": "978-0-553-29438-5",
            "price": 13.99,
            "stock": 18,
            "description": "A collection of nine science fiction short stories about robots and morality.",
            "publication_year": 1950,
            "pages": 253,
            "author_index": 3,
            "genre_index": 2,
        },
        {
            "title": "Murder on the Orient Express",
            "isbn": "978-0-06-269366-2",
            "price": 11.99,
            "stock": 35,
            "description": "A classic detective novel featuring Hercule Poirot investigating a murder on a train.",
            "publication_year": 1934,
            "pages": 256,
            "author_index": 4,
            "genre_index": 4,
        },
        {
            "title": "And Then There Were None",
            "isbn": "978-0-06-269373-0",
            "price": 10.99,
            "stock": 28,
            "description": "Ten strangers are lured to an island where they are killed one by one.",
            "publication_year": 1939,
            "pages": 272,
            "author_index": 4,
            "genre_index": 4,
        },
        {
            "title": "The ABC Murders",
            "isbn": "978-0-06-257369-8",
            "price": 12.49,
            "stock": 22,
            "description": "Hercule Poirot hunts a serial killer who murders in alphabetical order.",
            "publication_year": 1936,
            "pages": 256,
            "author_index": 4,
            "genre_index": 6,
        },
        {
            "title": "Tender Is the Night",
            "isbn": "978-0-684-80154-0",
            "price": 14.49,
            "stock": 15,
            "description": "A story of the rise and fall of Dick Diver, a promising young psychiatrist.",
            "publication_year": 1934,
            "pages": 320,
            "author_index": 0,
            "genre_index": 0,
        },
        {
            "title": "This Side of Paradise",
            "isbn": "978-0-486-28999-2",
            "price": 8.99,
            "stock": 12,
            "description": "Fitzgerald's debut novel about the education of a young man.",
            "publication_year": 1920,
            "pages": 305,
            "author_index": 0,
            "genre_index": 0,
        },
        {
            "title": "The End of Eternity",
            "isbn": "978-0-765-31919-0",
            "price": 16.99,
            "stock": 10,
            "description": "A science fiction novel about an organization that controls time travel.",
            "publication_year": 1955,
            "pages": 191,
            "author_index": 3,
            "genre_index": 2,
        },
        {
            "title": "Harry Potter and the Prisoner of Azkaban",
            "isbn": "978-0-7475-4215-5",
            "price": 21.99,
            "stock": 55,
            "description": "The third book in the Harry Potter series, introducing Sirius Black.",
            "publication_year": 1999,
            "pages": 317,
            "author_index": 2,
            "genre_index": 3,
        },
        {
            "title": "Down and Out in Paris and London",
            "isbn": "978-0-15-626224-1",
            "price": 11.49,
            "stock": 8,
            "description": "Orwell's memoir of living in poverty in two great European cities.",
            "publication_year": 1933,
            "pages": 213,
            "author_index": 1,
            "genre_index": 7,
        },
        {
            "title": "The Mysterious Affair at Styles",
            "isbn": "978-0-06-299394-4",
            "price": 9.49,
            "stock": 30,
            "description": "Agatha Christie's first published novel, introducing Hercule Poirot.",
            "publication_year": 1920,
            "pages": 296,
            "author_index": 4,
            "genre_index": 4,
        },
        {
            "title": "Homage to Catalonia",
            "isbn": "978-0-15-642117-1",
            "price": 13.49,
            "stock": 5,
            "description": "Orwell's personal account of his experiences in the Spanish Civil War.",
            "publication_year": 1938,
            "pages": 232,
            "author_index": 1,
            "genre_index": 8,
        },
        {
            "title": "The Caves of Steel",
            "isbn": "978-0-553-29340-1",
            "price": 12.99,
            "stock": 14,
            "description": "A science fiction detective novel set in a future Earth with humanoid robots.",
            "publication_year": 1954,
            "pages": 206,
            "author_index": 3,
            "genre_index": 2,
        },
        {
            "title": "The Beautiful and Damned",
            "isbn": "978-0-486-28994-7",
            "price": 7.99,
            "stock": 3,
            "description": "A portrait of the Jazz Age and the decline of a young couple.",
            "publication_year": 1922,
            "pages": 449,
            "author_index": 0,
            "genre_index": 0,
        },
        {
            "title": "Harry Potter and the Goblet of Fire",
            "isbn": "978-0-7475-4624-5",
            "price": 24.99,
            "stock": 60,
            "description": "The fourth Harry Potter novel, featuring the Triwizard Tournament.",
            "publication_year": 2000,
            "pages": 636,
            "author_index": 2,
            "genre_index": 3,
        },
    ]

    books: list[Book] = []
    for data in books_data:
        result = await db.execute(select(Book).where(Book.isbn == data["isbn"]))
        existing = result.scalars().first()
        if existing is not None:
            books.append(existing)
        else:
            book = Book(
                title=data["title"],
                isbn=data["isbn"],
                price=data["price"],
                stock=data["stock"],
                description=data["description"],
                publication_year=data["publication_year"],
                pages=data["pages"],
                author_id=authors[data["author_index"]].id,
                genre_id=genres[data["genre_index"]].id,
            )
            db.add(book)
            await db.flush()
            await db.refresh(book)
            books.append(book)
            print(f"Created book: {data['title']}")

    return books


async def seed() -> None:
    print("Creating database tables...")
    await create_tables()

    print("Seeding database...")
    async with SessionLocal() as db:
        try:
            await seed_admin(db)
            await seed_customer(db)
            genres = await seed_genres(db)
            authors = await seed_authors(db)
            await seed_books(db, authors, genres)
            await db.commit()
            print("Database seeding completed successfully.")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())