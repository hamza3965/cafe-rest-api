from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import random
import os

load_dotenv()

API_KEY = os.getenv("SECRET_API_KEY")  # Any random string

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)


def str_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "yes", "y", "true", "t"}


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


# HTTP GET - Read Record
@app.route("/random")
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    return jsonify(cafe=random_cafe.to_dict())


@app.route("/all")
def get_all_cafes():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


@app.route("/search")
def find_cafe():
    query_location = request.args.get("loc")
    result = db.session.execute(
        db.select(Cafe).where(Cafe.location.ilike(f"%{query_location}%"))
    )
    all_cafes = result.scalars().all()
    if all_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(
            error={"Not Found": "Sorry, we don't have a cafe at that location."}
        ), 404


# HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("location"),
        has_sockets=str_to_bool(request.form.get("has_sockets")),
        has_toilet=str_to_bool(request.form.get("has_toilet")),
        has_wifi=str_to_bool(request.form.get("has_wifi")),
        can_take_calls=str_to_bool(request.form.get("can_take_calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    try:
        print(
            f"Name = {request.form.get('name')}\n"
            f"Map URL = {request.form.get('map_url')}\n"
            f"Image URL = {request.form.get('img_url')}\n"
            f"Location = {request.form.get('location')}\n"
            f"Has Sockets = {request.form.get('has_sockets')}\n"
            f"Has Toilet = {request.form.get('has_toilet')}\n"
            f"Has Wifi = {request.form.get('has_wifi')}\n"
            f"Can Take Calls = {request.form.get('can_take_calls')}\n"
            f"Seats = {request.form.get('seats')}\n"
            f"Coffee Price = {request.form.get('coffee_price')}\n"
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(response={"error": "A cafe with this name already exists."}), 409
    else:
        return jsonify(response={"success": "Successfully added the new cafe."}), 201


# HTTP PUT/PATCH - Update Record
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def update_price(cafe_id):
    new_price = request.args.get("new-price")
    cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
    if cafe:
        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(success="Successfully updated the price."), 200
    else:
        return jsonify(
            error={
                "Not Found": "Sorry a cafe with that id was not found in the database"
            }
        ), 404


# HTTP DELETE - Delete Record
@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    user_api_key = request.args.get("api-key")
    if user_api_key == API_KEY:
        cafe = db.session.execute(db.select(Cafe).where(Cafe.id == cafe_id)).scalar()
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(
                response={"success": "Successfully deleted the cafe from the database."}
            ), 200
        else:
            return jsonify(
                error={
                    "Not Found": "Sorry a cafe with that id was not found in the database."
                }
            ), 404
    else:
        return jsonify(
            error={
                "Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."
            }
        ), 403


if __name__ == "__main__":
    app.run(debug=True)
