import gradio as gr
import time
from datetime import datetime

# Walmart-like color scheme
walmart_blue = "#0071ce"
walmart_yellow = "#ffc220"
walmart_light_blue = "#e6f2ff"

# Custom CSS for Walmart-like theme
custom_css = """
.gradio-container {
    background-color: #f0f2f5;
    font-family: 'Bogle', Arial, sans-serif;
}
.action-button {
    background-color: #0071ce !important;
    color: white !important;
    border: none !important;
    padding: 10px 20px !important;
    border-radius: 4px !important;
    font-weight: bold !important;
    cursor: pointer !important;
    transition: background-color 0.3s !important;
}
.action-button:hover {
    background-color: #004c91 !important;
}
.header-title {
    color: #0071ce;
    font-size: 2.5em;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
}
.status-box {
    background-color: #e6f2ff;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #0071ce;
}
.success-message {
    background-color: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
    padding: 15px;
    border-radius: 4px;
    margin: 10px 0;
}
.error-message {
    background-color: #f8d7da;
    border-color: #f5c6cb;
    color: #721c24;
    padding: 15px;
    border-radius: 4px;
    margin: 10px 0;
}
.main-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}
"""

# Simulated database for orders
orders_db = {
    "12345": {"customer": "John Doe", "amount": 149.99, "items": ["TV Stand", "HDMI Cable"]},
    "67890": {"customer": "Jane Smith", "amount": 89.50, "items": ["Bluetooth Speaker"]},
    "11111": {"customer": "Bob Johnson", "amount": 234.00, "items": ["Gaming Console", "Extra Controller"]}
}

def process_refund(order_id, refund_amount, customer_name):
    """Process refund request"""
    # Simulate processing time
    time.sleep(1)
    
    if order_id in orders_db:
        order = orders_db[order_id]
        if float(refund_amount) <= order["amount"]:
            success_msg = f"""<div class='success-message'>
            <h3>✅ REFUND PROCESSED</h3>
            <p>Refund of <strong>${refund_amount}</strong> has been sent to <strong>{customer_name}</strong></p>
            <p>Transaction ID: REF-{int(time.time())}</p>
            <p>You will receive a confirmation email shortly.</p>
            </div>"""
            return success_msg
        else:
            error_msg = f"""<div class='error-message'>
            <h3>❌ REFUND FAILED</h3>
            <p>Refund amount exceeds order total (${order['amount']})</p>
            <p>Please enter an amount less than or equal to the order total.</p>
            </div>"""
            return error_msg
    else:
        error_msg = f"""<div class='error-message'>
        <h3>❌ ORDER NOT FOUND</h3>
        <p>No order found with ID: {order_id}</p>
        <p>Please check the order ID and try again.</p>
        </div>"""
        return error_msg

def process_price_match(order_id, competitor_price, competitor_name):
    """Process price match request"""
    # Simulate processing time
    time.sleep(1)
    
    if order_id in orders_db:
        order = orders_db[order_id]
        current_price = order["amount"]
        comp_price = float(competitor_price)
        
        if comp_price < current_price:
            difference = current_price - comp_price
            success_msg = f"""<div class='success-message'>
            <h3>✅ PRICE MATCH APPROVED</h3>
            <p>Original Price: <strong>${current_price}</strong></p>
            <p>Competitor ({competitor_name}) Price: <strong>${comp_price}</strong></p>
            <p>Refund Amount: <strong>${difference:.2f}</strong></p>
            <p>The price difference has been credited to your account.</p>
            </div>"""
            return success_msg
        else:
            error_msg = f"""<div class='error-message'>
            <h3>❌ PRICE MATCH DENIED</h3>
            <p>Competitor price (${comp_price}) is not lower than current price (${current_price})</p>
            <p>We only match prices that are lower than our current price.</p>
            </div>"""
            return error_msg
    else:
        error_msg = f"""<div class='error-message'>
        <h3>❌ ORDER NOT FOUND</h3>
        <p>No order found with ID: {order_id}</p>
        <p>Please check the order ID and try again.</p>
        </div>"""
        return error_msg

def process_cancel_order(order_id):
    """Process order cancellation"""
    # Simulate processing time
    time.sleep(1)
    
    if order_id in orders_db:
        order = orders_db[order_id]
        items_list = ", ".join(order['items'])
        success_msg = f"""<div class='success-message'>
        <h3>✅ ORDER CANCELLED</h3>
        <p>Order <strong>{order_id}</strong> has been cancelled</p>
        <p>Customer: <strong>{order['customer']}</strong></p>
        <p>Items: {items_list}</p>
        <p>Refund Amount: <strong>${order['amount']}</strong></p>
        <p>Refund will be processed within 3-5 business days.</p>
        </div>"""
        # Remove order from database
        del orders_db[order_id]
        return success_msg
    else:
        error_msg = f"""<div class='error-message'>
        <h3>❌ ORDER NOT FOUND</h3>
        <p>No order found with ID: {order_id}</p>
        <p>Please check the order ID and try again.</p>
        </div>"""
        return error_msg

# Create Gradio interface
with gr.Blocks(css=custom_css, theme=gr.themes.Base()) as demo:
    gr.HTML('<div class="header-title">🛒 M<span style="color: #ffc220;">A</span>LWART Customer Service Portal</div>')
    
    with gr.Row():
        with gr.Column(scale=1, elem_classes=["main-container"]):
            
            with gr.Tab("Cancel Order"):
                gr.Markdown("### 🚫 Cancel Your Order")
                order_id_cancel = gr.Textbox(
                    label="Order ID",
                    placeholder="Enter your order ID"
                )
                cancel_btn = gr.Button(
                    "Cancel Order",
                    elem_classes=["action-button"],
                    variant="primary"
                )
                cancel_output = gr.HTML(
                    label="Result"
                )
            
            with gr.Tab("Price Match"):
                gr.Markdown("### 💰 Request Price Match")
                order_id_price = gr.Textbox(
                    label="Order ID",
                    placeholder="Enter your order ID"
                )
                competitor_name = gr.Textbox(
                    label="Competitor Name",
                    placeholder="e.g., BestBuy, Target, Amazon"
                )
                competitor_price = gr.Number(
                    label="Competitor Price ($)",
                    precision=2
                )
                price_match_btn = gr.Button(
                    "Process Price Match",
                    elem_classes=["action-button"],
                    variant="primary"
                )
                price_match_output = gr.HTML(
                    label="Result"
                )
            
            with gr.Tab("Refund"):
                gr.Markdown("### 💸 Process Refund")
                order_id_refund = gr.Textbox(
                    label="Order ID",
                    placeholder="Enter your order ID"
                )
                customer_name = gr.Textbox(
                    label="Customer Name",
                    placeholder="Enter your full name"
                )
                refund_amount = gr.Number(
                    label="Refund Amount ($)",
                    precision=2
                )
                refund_btn = gr.Button(
                    "Process Refund",
                    elem_classes=["action-button"],
                    variant="primary"
                )
                refund_output = gr.HTML(
                    label="Result"
                )
    
    # Connect buttons to handlers
    cancel_btn.click(
        process_cancel_order,
        inputs=[order_id_cancel],
        outputs=[cancel_output]
    )
    
    price_match_btn.click(
        process_price_match,
        inputs=[order_id_price, competitor_price, competitor_name],
        outputs=[price_match_output]
    )
    
    refund_btn.click(
        process_refund,
        inputs=[order_id_refund, refund_amount, customer_name],
        outputs=[refund_output]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(server_name="localhost", server_port=7866, share=True)