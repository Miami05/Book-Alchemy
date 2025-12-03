from flask import Flask, request, render_template, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from openai import OpenAI
from data_models import db, Author, Book
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)


basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-only')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
db.init_app(app)


@app.route('/', methods=['GET'])
def home():
    """Display all books with optional sorting and search functionality."""
    sort = request.args.get('sort', 'title')
    search_query = request.args.get('search', '')
    query = Book.query
    if search_query:
        query = query.filter(Book.title.ilike(f"%{search_query}%"))
    if sort == 'author':
        books = query.join(Author).order_by(Author.name.asc()).all()
    else:
        books = query.order_by(Book.title.asc()).all()
    return render_template('home.html', books=books, sort_by=sort, search_query=search_query)


@app.route("/recommend", methods=["GET"])
def recommend():
    """Generate AI-powered book recommendations based on user's library."""
    books = Book.query.all()
    lines = []
    for b in books:
        line = f"- {b.title}"
        if b.author:
            line += f" by {b.author.name}"
        if getattr(b, "rating", None):
            line += f" (rating: {b.rating}/10)"
        lines.append(line)

    library_description = "\n".join(lines) if lines else "No books yet."
    prompt = (
      "You are a helpful book recommendation assistant.\n"
      "Here is the list of books I have read:\n"
      f"{library_description}\n\n"
      "Based on this list, suggest ONE book I should read next and explain why "
      "in 2–3 short sentences. Do not use tables or formatting, just plain text."
    )
    ai_response_text = None
    if client.api_key:
        try:
            response = client.responses.create(
                input=prompt,
                model="openai/gpt-oss-20b",
            )
            ai_response_text = response.output_text
        except Exception as e:
            ai_response_text = f"Error contacting Groq API: {e}"
    else:
        ai_response_text = "No GROQ_API_KEY configured in the environment."
    return render_template(
        "recommend.html",
        books=books,
        ai_response=ai_response_text,
        library_description=library_description,
    )


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """Handle GET/POST requests for adding new authors to the database."""
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date = request.form.get('birthdate')
        date_of_death = request.form.get('date_of_death')
        
        if not name or not birth_date:
            flash("Name and birth date are required", "error")
            return render_template('add_author.html')
        
        try:
            new_author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death
            )
            db.session.add(new_author)
            db.session.commit()
            flash("Author added successfully!", 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding author: {str(e)}", 'error')
        
        return redirect('/add_author')
    return render_template('add_author.html')


@app.route('/book/<int:book_id>/delete', methods=["POST"])
def delete_book(book_id):
    """Delete a specific book and its author if no other books remain."""
    book = Book.query.get_or_404(book_id)
    author = book.author
    
    try:
        db.session.delete(book)
        db.session.commit()
        
        if author and not author.books:
            db.session.delete(author)
            db.session.commit()
            flash(f"Book '{book.title}' and author '{author.name}' deleted successfully!", 'success')
        else:
            flash(f"Book '{book.title}' deleted successfully!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting book: {str(e)}", 'error')
    
    return redirect('/')


@app.route('/book/<int:book_id>', methods=['GET'])
def book_detail(book_id):
    """Display detailed information for a specific book."""
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)


@app.route('/author/<int:author_id>', methods=['GET'])
def author_detail(author_id):
    """Display detailed information for a specific author."""
    author = Author.query.get_or_404(author_id)
    return render_template('author_detail.html', author=author)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """Handle GET/POST requests for adding new books to the database."""
    authors = Author.query.all()
    
    if request.method == 'POST':
        title = request.form['title']
        isbn = request.form.get('isbn')
        publication_year = request.form.get('publication_year')
        author_id = request.form['author_id']
        rating_raw = request.form.get('rating')
        
        try:
            rating = int(rating_raw) if rating_raw else None
        except ValueError:
            flash("Invalid rating. Please enter a number between 1-10.", "error")
            return redirect('/add_book')
        
        try:
            new_book = Book(
                title=title,
                isbn=isbn,
                publication_year=publication_year or None,
                author_id=author_id,
                rating=rating
            )
            db.session.add(new_book)
            db.session.commit()
            flash("Book added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding book: {str(e)}", 'error')
        
        return redirect('/add_book')
    
    return render_template('add_book.html', authors=authors)


@app.route('/author/<int:author_id>/delete', methods=['POST'])
def delete_author(author_id):
    """Delete an author and all their books via cascade."""
    author = Author.query.get_or_404(author_id)
    
    try:
        db.session.delete(author)
        db.session.commit()
        flash(f"Author '{author.name}' and all their books were deleted", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting author: {str(e)}", "error")
    
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)
