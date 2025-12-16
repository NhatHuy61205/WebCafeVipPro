from flask import Flask, render_template
from CafeApp import app
from CafeApp.models import Mon


@app.route("/")
def index():
    ds_mon = Mon.query.all()
    return render_template("index.html", items=ds_mon)

@app.route("/menu")
def menu():
    ds_mon = Mon.query.all()
    return render_template("layout/menu.html", items=ds_mon)

@app.route("/login")
def login():
    return render_template("layout/login.html")

@app.route("/pos")
def pos_page():
    # 1. Kiểm tra quyền nhân viên
    if session.get('role') != 'NHAN_VIEN':
        return redirect(url_for('login'))
        
    # 2. Lấy danh sách món ăn từ DB
    ds_mon = Mon.query.all()
    
    # 3. Lấy dữ liệu giỏ hàng từ hàm get_cart_data() vừa tạo
    data = get_cart_data()
    
    # 4. Gửi tất cả sang HTML (QUAN TRỌNG: Phải có cart_session)
    return render_template("pos.html", 
                           items=ds_mon, 
                           cart=data['cart'], 
                           total=data['total'], 
                           cart_session=data['cart_session'])

def get_cart_data():
    cart_session = session.get('pos_cart', {})
    cart_list = []
    total_price = 0
    
    if cart_session:
        # Lấy thông tin chi tiết các món trong giỏ
        products = Mon.query.filter(Mon.id.in_(cart_session.keys())).all()
        for p in products:
            qty = cart_session[str(p.id)]
            item_total = p.gia * qty
            total_price += item_total
            
           
            cart_list.append({
                'product': p,     
                'quantity': qty,
                'total_price': item_total
            })
            
    # Trả về cục dữ liệu JSON
    return {
        'cart': cart_list,
        'total': total_price,
        'cart_session': cart_session # Để biết món nào đang được chọn (ID và SL)
    }

@app.route('/api/pos/update', methods=['POST'])
def api_pos_update():
    data = request.json # Nhận dữ liệu từ JS gửi lên
    p_id = str(data.get('product_id'))
    action = data.get('action') # 'add', 'increase', 'decrease', 'remove'
    
    cart = session.get('pos_cart', {})
    
    if action == 'add':
        if p_id in cart: cart[p_id] += 1
        else: cart[p_id] = 1
        
    elif action == 'increase':
        if p_id in cart: cart[p_id] += 1
        
    elif action == 'decrease':
        if p_id in cart:
            cart[p_id] -= 1
            if cart[p_id] < 1: del cart[p_id]
            
    elif action == 'remove':
        if p_id in cart: del cart[p_id]
        
    elif action == 'clear':
        cart = {}

    session['pos_cart'] = cart
    
    # Trả về dữ liệu mới nhất để giao diện tự cập nhật
    return jsonify(get_cart_data())

@app.route("/admin")
def admin_dashboard():
    # Kiểm tra quyền Admin
    if session.get('role') not in ['QUAN_LY_CUA_HANG', 'QUAN_LY_KHO']:
        return redirect(url_for('login'))
        
    return render_template("admin/dashboard.html")

if __name__=="__main__":
    with app.app_context():
        app.run(debug=True)