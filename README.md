# OTEL Examples

This repository contains example implementations for event-driven microservices using OpenTelemetry (OTEL) for observability. These services showcase a simple e-commerce system, with components for orders, payments, invoicing, and notifications, all instrumented for distributed tracing.

## Overview

This system is composed of the following microservices, using NATS for asynchronous communication:

1. **Orders Service**
   - Handles CRUD operations for orders.
   - Listens to the `paid` event to mark orders as paid.
   - Sends a `complete` event when the order is processed.

2. **Payment Service**
   - Processes payments for orders.
   - Emits a `paid` event after a successful transaction.

3. **Invoice Service**
   - Generates invoices upon receiving the `complete` event.
   - Stores the invoice in MinIO and sends a `notify` event.

4. **Notification Service**
   - Sends invoices to customers via email.
   - Listens for the `notify` event from the Invoice service.

## Components

- **NATS**: Used as the message broker for communication between services.
- **Redis**: Provides a cache-aside strategy for Orders.
- **Postgres**: Serves as the main storage for the Orders service.
- **MinIO**: Object storage used to store generated invoices.
- **OpenTelemetry**: Integrated to collect and forward telemetry data to a collector for distributed tracing and performance monitoring.

### OpenTelemetry Collector

All microservices are instrumented with OTEL to send telemetry data (spans, traces, metrics) to an OTEL Collector, which can then be visualized using tools like Jaeger or Grafana.

## Architecture Diagram

The following diagram represents the flow of events and interactions between the services:

![Architecture](https://github.com/user-attachments/assets/4546862b-9268-4d8d-b0e3-d88ff2e95a62)

## Running the Examples

### Prerequisites

- [NATS](https://nats.io/) - Event broker for messaging between services.
- [Redis](https://redis.io/) - For caching in the Orders service.
- [Postgres](https://www.postgresql.org/) - Database for the Orders service.
- [MinIO](https://min.io/) - Object storage for invoices.
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) - For tracing and observability.
  
### Steps to Run

*To be added: Detailed steps on running the services and setting up the infrastructure.*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
