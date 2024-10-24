use serde::Deserialize;

#[derive(Deserialize, Debug)]
pub struct PaymentPayload {
    pub order_id: String,
}
