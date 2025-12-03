from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Author(db.Model):
    """
    Represents an author in the library database.
    
    Attributes:
        id: Primary key identifier
        name: Author's full name
        birth_date: Date of birth (stored as DATE type)
        date_of_death: Date of death (nullable for living authors, stored as DATE type)
        books: Relationship to Book objects with cascade delete
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)
    books = db.relationship(
        'Book',
        backref='author',
        cascade='all, delete-orphan',
        lazy=True
    )
    
    def __str__(self):
        """Return a human-readable string representation of the author."""
        death = self.date_of_death if self.date_of_death else "Present"
        return f"{self.name} ({self.birth_date} - {death})"
    
    def __repr__(self):
        """Return a detailed string representation for debugging."""
        return f"<Author {self.name}>"


class Book(db.Model):
    """
    Represents a book in the library database.
    
    Attributes:
        id: Primary key identifier
        isbn: International Standard Book Number (unique)
        title: Book title
        publication_year: Year the book was published
        author_id: Foreign key reference to Author
        rating: User rating from 1-10
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(500), nullable=False)
    publication_year = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    rating = db.Column(db.Integer)

    def __str__(self):
        """Return a human-readable string representation of the book."""
        return f"{self.title} ({self.publication_year})"

    def __repr__(self):
        """Return a detailed string representation for debugging."""
        return f"<Book {self.title} ISBN = {self.isbn}>"
