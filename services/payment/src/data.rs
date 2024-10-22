use serde::Deserialize;

#[derive(Deserialize)]
pub struct PaymentPayload {
    pub order_id: String,
}
