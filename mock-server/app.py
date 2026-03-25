from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# Load customer data from JSON file at startup
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "customers.json")

def load_customers():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


#Health Check

@app.route("/api/health", methods=["GET"])
def health():
    customers = load_customers()
    return jsonify({"status": "ok", "service": "mock-server", "total_customers": len(customers)}), 200


# Customers list (Paginated) 

@app.route("/api/customers", methods=["GET"])
def get_customers():
    customers = load_customers()

    try:
        page  = int(request.args.get("page",  1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "page and limit must be integers"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "page and limit must be >= 1"}), 400

    start = (page - 1) * limit
    end   = start + limit
    slice_ = customers[start:end]

    return jsonify({
        "data":  slice_,
        "total": len(customers),
        "page":  page,
        "limit": limit
    }), 200


# Single Customer

@app.route("/api/customers/<string:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customers = load_customers()
    customer = next(
        (c for c in customers if c["customer_id"] == customer_id), None
    )
    if customer is None:
        return jsonify({"error": f"Customer '{customer_id}' not found"}), 404

    return jsonify(customer), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
