from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float, DateTime, JSON
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from form import AuctionItemForm, LoginForm, SignupForm
from datetime import datetime, timedelta
import os

def search_and_sort(my_bids=False):
    sort = request.args.get('sort','latest')
    if sort == 'ending_soon':
        result = db.select(Product).order_by(Product.end_time)
    elif sort == 'low_to_high':
        result = db.select(Product).order_by(Product.price)
    elif sort == 'high_to_low':
        result = db.select(Product).order_by(Product.price.desc())
    elif sort == 'most_bids':
        result = db.select(Product).order_by(Product.price.desc())
    else:
        result = db.select(Product).order_by(Product.id.desc())

    cat = request.args.get('category','').title()
    search = request.args.get('q','')

    if cat != '':
        query = result.where((Product.tag == cat) & (Product.end_time > datetime.now()))
    else:
        query = result.where((Product.end_time > datetime.now()))

    if my_bids:
        bids = db.session.execute(db.select(Bid.product_id).where(Bid.bidder_id == current_user.id)).scalars().all()
        p = db.session.execute(query.where(Product.id.in_(bids))).scalars().all()
    else:
        p = db.session.execute(query).scalars().all()

    products = []

    status = request.args.get("status")

    #done so that titles matching the search query show up first, basically the most relevant items (according to the search query) will show up first
    for i in range(0, len(p)):

        flag = True

        if my_bids:
            if status == "losing_bids":
                if p[i].bids[-1].bidder == current_user:
                    flag = False

            elif status == "winning_bids":
                if p[i].bids[-1].bidder != current_user:
                    flag = False

        if search in p[i].title.lower().split(' ') and flag:
            products.append(p[i])

    for i in range(0,len(p)):

        flag = True

        if my_bids:
            if status == "losing_bids":
                if p[i].bids[-1].bidder == current_user:
                    flag = False

            elif status == "winning_bids":
                if p[i].bids[-1].bidder != current_user:
                    flag = False

        if ((search not in p[i].title.lower().split(' ')) and ((search in p[i].subtitle.lower().split(' ')) or (search in p[i].description.lower().split(' ')) or (search in p[i].location.lower().split(' ')) or search=='')) and flag:
            products.append(p[i])

    t = db.session.execute(db.select(Tag).order_by(Tag.id)).scalars()
    tags = t.all()

    return products,tags

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="seller")
    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="bidder")

class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[datetime] = mapped_column(default=datetime.now())
    end_time: Mapped[datetime] = mapped_column(DateTime)
    duration: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    shipping: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(default="active")
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    seller_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    seller: Mapped["User"] = relationship("User", back_populates="products")
    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="product")

class Bid(db.Model):
    __tablename__ = "bids"
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    bid_time: Mapped[datetime] = mapped_column(default=datetime.now())

    bidder_id: Mapped[int] = mapped_column(Integer,db.ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(Integer,db.ForeignKey("products.id"))

    bidder: Mapped["User"] = relationship("User", back_populates="bids")
    product: Mapped["Product"] = relationship("Product", back_populates="bids")

class Tag(db.Model):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

with app.app_context():
    db.create_all()

@app.route("/payment")
def payment():
    return render_template("paymet.html")

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email==form.email.data))
        user = result.scalar()

        if not user:
            flash("Account doesn't exist. Please try again.")
            return redirect(url_for("login"))

        elif not check_password_hash(user.password, password):
            flash("Password is incorrect. Please try again.")
            return redirect(url_for("login"))

        else:
            login_user(user)
            return redirect(url_for("home"))

    return render_template("login.html", form=form)

@app.route("/signup", methods=["GET","POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        registered_user = result.scalar()

        if registered_user:
            flash("Account already exists. Please login instead.")
            return redirect(url_for("login"))

        password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        user = User(
            name = form.name.data,
            email=form.email.data,
            password=password,
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        return redirect(url_for('home'))

    return render_template("register.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/")
def home():
    result = db.session.execute(db.select(Product).where(Product.end_time>datetime.now())).scalars()
    products = result.all()

    n = len(products)
    if n>9:
        n=9

    return render_template("index.html",products=products,n=n)

@app.route("/auctions")
def auction():
    products,tags = search_and_sort()
    return render_template("auctions.html", products=products, tags=tags)

@app.route("/my_bids")
def my_bid():
    my_bids = True
    products,tags = search_and_sort(my_bids=my_bids)
    return render_template("auctions.html", products=products, tags=tags, my_bids=my_bids)

@app.route("/add-product",methods=["GET","POST"])
@login_required
def add_product():
    form = AuctionItemForm()
    if form.validate_on_submit():
        tag = form.tag.data
        if tag=="other":
            tag = form.other.data

        product = Product(
            tag = tag,
            title = form.title.data,
            subtitle = form.subtitle.data,
            description = form.description.data,
            #img = form.img.data,
            price = form.price.data,
            duration=form.duration.data,
            #date=date.today().strftime("%d/%m/%Y"),
            end_time = datetime.now() + timedelta(hours=int(form.duration.data)),
            location = form.location.data,
            shipping = form.shipping.data,
            seller = current_user
        )

        db.session.add(product)
        db.session.commit()

        product = db.session.execute(db.select(Product).order_by(Product.id.desc())).scalars().all()[0]

        files = request.files.getlist('img')

        folder = secure_filename(str(product.id))
        path = os.path.join('static', 'images', folder)
        os.makedirs(path, exist_ok=True)

        if files:
            for i, file in enumerate(files):
                if file and file.filename != '':
                    ext = os.path.splitext(file.filename)[1]
                    name = f"img_{i+1}{ext}"
                    img = os.path.join(path, name)
                    file.save(img)

        prod = db.get_or_404(Product,product.id)
        files = os.listdir(f"static/images/{product.id}")
        prod.images = files
        db.session.commit()

        t = db.session.execute(db.select(Tag).where(Tag.name==tag)).scalar()
        if not t:
            new_tag = Tag(name = tag.title())
            db.session.add(new_tag)
            db.session.commit()
        return redirect(url_for('home'))

    return render_template("add-product.html",form = form)

@app.route("/item/<int:id>",methods=["GET","POST"])
def item(id):
    product = db.get_or_404(Product, id)
    bid = request.form.get('bid')

    if request.method == 'POST':
        if bid!='':
            if current_user.is_authenticated:
                if float(bid)<product.price:
                    flash("Enter a higher price than the one listed")
                    return redirect(url_for('item',id=id))

                bidding = Bid(
                    amount=bid,
                    bidder=current_user,
                    product=product
                )

                db.session.add(bidding)
                product.price = product.bids[-1].amount
                db.session.commit()
                return redirect(url_for("item",id=id))

            else:
                flash("Log-in to participate")
                return redirect(url_for("login"))

        else:
            flash("Enter an actual price")
            return redirect(url_for("item",id=id))

    end_date = product.end_time.strftime("%B %d, %Y (%I:%M %p)")
    return render_template("item.html", product=product, date=datetime.now(), end = end_date)

if __name__ == "__main__":
    app.run(debug=True, port=5002)