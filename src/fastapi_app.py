from fastapi import FastAPI, Form, HTTPException, Request, Depends
from pydantic import BaseModel
from src.utils.modulbank_api import ModulBankApi
from src.db.repositories.order import OrderRepository
from src.context import AppContext
import uuid

app = FastAPI(root_path="/reader")

class PaymentRequest(BaseModel):
    custom_order_id: str
    signature: str

def get_context() -> AppContext:
    if not hasattr(app.state, "context"):
        raise HTTPException(status_code=500, detail="Application context is not initialized.")
    return app.state.context

@app.post("/modulbank")
async def finish_order(
    request: Request,
    custom_order_id: str = Form(...),
    signature: str = Form(...),
    context: AppContext = Depends(get_context),
):
    # Extract form data
    form_data = await request.form()
    data = {key: value for key, value in form_data.items()}

    # Validate signature
    modulbank_api: ModulBankApi = context["modulbank_api"]
    calculated_signature = modulbank_api.get_signature(data)
    if signature != calculated_signature:
        raise HTTPException(status_code=401, detail="Invalid signature.")

    # Process the order
    order_uuid = uuid.UUID(custom_order_id)
    order_repository: OrderRepository = OrderRepository(
        context["db_pool"], context["db_logger"]
    )
    await order_repository.update_order_is_paid(str(order_uuid), True)

    return {"status": "success", "message": "Payment processed successfully."}