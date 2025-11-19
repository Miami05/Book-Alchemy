from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    birth_date = db.Column(db.Text)
    date_of_death = db.Column(db.Text)
    books = db.relationship(
      'Book',
      backref='author',
      cascade='all, delete',
      lazy=True
      )
    def __str__(self):
        return f"{self.name} ({self.birth_date} - {self.date_of_death})"
    def __repr__(self):
        return f"<Author {self.name}>"

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20))
    title = db.Column(db.Text, nullable=False)
    publication_year = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    rating = db.Column(db.Integer)

    def __str__(self):
        return f"{self.title} ({self.publication_year})"

    def __repr__(self):
        return f"<Book {self.title} ISBN = {self.isbn}>"

