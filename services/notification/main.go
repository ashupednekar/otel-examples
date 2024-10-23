package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"mime/quotedprintable"
	"net/http"
	"net/smtp"
	"net/textproto"
	"os"
	"path/filepath"
	"strings"

	"github.com/nats-io/nats.go"
)

type EmailPayload struct {
	To          string   `json:"to"`
	Subject     string   `json:"subject"`
  Body        string   `json:"body"`
	Attachments []string `json:"attachments"`
}

func main() {
	natsURL := os.Getenv("NATS_URL")
	nc, err := nats.Connect(natsURL)
	if err != nil {
		log.Fatalf("Error connecting to NATS: %v", err)
	}
	defer nc.Close()

	js, err := nc.JetStream()
	if err != nil {
		log.Fatalf("Error getting JetStream context: %v", err)
	}

	_, err = js.AddStream(&nats.StreamConfig{
		Name:     "messaging",
		Subjects: []string{"message.>"},
		Storage:  nats.FileStorage,
	})
	if err != nil && err != nats.ErrStreamNameAlreadyInUse {
		log.Fatalf("Error adding stream: %v", err)
	}

	subscription, err := js.Subscribe("message.send", messageHandler)
	if err != nil {
		log.Fatalf("Error subscribing to subject: %v", err)
	}

	log.Printf("Listening for messages on subject: %s", subscription.Subject)
	select {}
}

func messageHandler(msg *nats.Msg) {
	var payload EmailPayload
	if err := json.Unmarshal(msg.Data, &payload); err != nil {
		log.Printf("Error unmarshaling message: %v", err)
		return
	}

	payload.Subject = "Order Processed"
	payload.Body = "Your order has been processed successfully with the pdf attachment."

	if err := sendEmail(payload); err != nil {
		log.Printf("Error sending email: %v", err)
		return
	}

	log.Printf("Email sent to: %s", payload.To)
}

func sendEmail(payload EmailPayload) error {
	from := os.Getenv("SMTP_EMAIL")
	to := payload.To
	subject := payload.Subject

	var attachments []string
	for _, attachmentURL := range payload.Attachments {
		attachmentPath, err := downloadAttachment(attachmentURL)
		if err != nil {
			return fmt.Errorf("error downloading attachment: %v", err)
		}
		attachments = append(attachments, attachmentPath)
		log.Printf("Downloaded attachment: %s", attachmentPath)
	}

	emailBody, err := createEmailBody(from, to, subject, attachments)
	if err != nil {
		return err
	}

	smtpHost := "smtp.gmail.com"
	smtpPort := "587"
	password := os.Getenv("SMTP_PASS")

	auth := smtp.PlainAuth("", from, password, smtpHost)

	err = smtp.SendMail(smtpHost+":"+smtpPort, auth, from, []string{to}, emailBody)
	if err != nil {
		return fmt.Errorf("error sending email: %v", err)
	}

	return nil
}

func createEmailBody(from, to, subject string, attachments []string) ([]byte, error) {
	var emailBody bytes.Buffer
	writer := multipart.NewWriter(&emailBody)

	headers := make(textproto.MIMEHeader)
	headers.Set("From", from)
	headers.Set("To", to)
	headers.Set("Subject", subject)
	headers.Set("MIME-Version", "1.0")
	headers.Set("Content-Type", "multipart/mixed; boundary="+writer.Boundary())

	header := make([]byte, 0)
	for k, v := range headers {
		header = append(header, []byte(fmt.Sprintf("%s: %s\r\n", k, strings.Join(v, ",")))...)
	}
	emailBody.Write(header)

	partWriter, _ := writer.CreatePart(textproto.MIMEHeader{
		"Content-Type":              {"text/plain; charset=UTF-8"},
		"Content-Transfer-Encoding": {"quoted-printable"},
	})
	qp := quotedprintable.NewWriter(partWriter)
	qp.Write([]byte("Your order has been processed successfully with the pdf attachment.\n"))
	qp.Close()

	for _, attachment := range attachments {
		err := addAttachment(writer, attachment)
		if err != nil {
			return nil, fmt.Errorf("error adding attachment: %v", err)
		}
	}

	writer.Close()
	return emailBody.Bytes(), nil
}

func addAttachment(writer *multipart.Writer, filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("error opening attachment: %v", err)
	}
	defer file.Close()

	part, err := writer.CreatePart(textproto.MIMEHeader{
		"Content-Type":              {"application/pdf"},
		"Content-Transfer-Encoding": {"base64"},
		"Content-Disposition":       {"attachment; filename=\"" + filepath.Base(filePath) + "\""},
	})
	if err != nil {
		return fmt.Errorf("error creating attachment part: %v", err)
	}

	encoder := base64.NewEncoder(base64.StdEncoding, part)
	_, err = io.Copy(encoder, file)
	if err != nil {
		return fmt.Errorf("error encoding attachment: %v", err)
	}
	encoder.Close()

	return nil
}

func downloadAttachment(url string) (string, error) {
	resp, err := http.Get(url)
	if err != nil {
		return "", fmt.Errorf("failed to download attachment: %v", err)
	}
	defer resp.Body.Close()

	file, err := os.Create("attachment.pdf")
	if err != nil {
		return "", fmt.Errorf("failed to create file: %v", err)
	}
	defer file.Close()

	if _, err := io.Copy(file, resp.Body); err != nil {
		return "", fmt.Errorf("failed to save attachment: %v", err)
	}

	return file.Name(), nil
}
