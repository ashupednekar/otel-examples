package main

import (
	"encoding/json"
	"log"
	"net/smtp"
	"os"

	"github.com/nats-io/nats.go"
)

type EmailPayload struct {
	To      string `json:"to"`
	Subject string `json:"subject"`
	Body    string `json:"body"`
}

func sendEmail(email EmailPayload) error {
	smtpHost := "smtp.gmail.com"
	smtpPort := "587"
	auth := smtp.PlainAuth("", os.Getenv("SMTP_EMAIL"), os.Getenv("SMTP_PASS"), smtpHost)
	msg := []byte("To: " + email.To + "\r\n" +
		"Subject: " + email.Subject + "\r\n" +
		"\r\n" +
		email.Body + "\r\n")
	err := smtp.SendMail(smtpHost+":"+smtpPort, auth, os.Getenv("SMTP_EMAIL"), []string{email.To}, msg)
	if err != nil {
		return err
	}
	return nil
}

func main() {
	nc, err := nats.Connect(os.Getenv("NATS_URL"))
	if err != nil {
		log.Fatal(err)
	}
	defer nc.Close()
	js, err := nc.JetStream()
	if err != nil {
		log.Fatal(err)
	}
	_, err = js.Subscribe("message.send", func(m *nats.Msg) {
		var email EmailPayload
		if err := json.Unmarshal(m.Data, &email); err != nil {
			log.Printf("Error parsing email payload: %v\n", err)
			return
		}
		if err := sendEmail(email); err != nil {
			log.Printf("Failed to send email: %v\n", err)
		} else {
			log.Printf("Email sent to %s\n", email.To)
		}
		m.Ack()
	}, nats.ManualAck())
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Listening for messages...")
	select {}
}
