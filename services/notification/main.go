package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/smtp"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"github.com/nats-io/nats.go"
)

type EmailPayload struct {
	To          string   `json:"to"`
	Subject     string   `json:"subject"`
	Body        string   `json:"body"`
	Attachments []string `json:"attachments"`
}

func createOrGetStream(js nats.JetStreamContext) error {
	streamName := "workqueue"
	stream, err := js.StreamInfo(streamName)
	if err != nil || stream == nil {
		_, err := js.AddStream(&nats.StreamConfig{
			Name:     streamName,
			Subjects: []string{"message.send"},
		})
		if err != nil {
			return fmt.Errorf("error creating stream: %v", err)
		}
		log.Printf("Stream %s created", streamName)
	} else {
		log.Printf("Stream %s exists", streamName)
	}
	return nil
}

func downloadFile(url string, wg *sync.WaitGroup, ch chan string) {
	defer wg.Done()
	resp, err := http.Get(url)
	if err != nil {
		log.Printf("Failed to download file: %v\n", err)
		ch <- ""
		return
	}
	defer resp.Body.Close()

	fileName := filepath.Base(strings.Split(url, ".pdf")[0])
	file, err := os.Create(fileName)
	if err != nil {
		log.Printf("Failed to create file: %v\n", err)
		ch <- ""
		return
	}
	defer file.Close()

	_, err = io.Copy(file, resp.Body)
	if err != nil {
		log.Printf("Failed to write file: %v\n", err)
		ch <- ""
		return
	}

	ch <- fileName
}

func sendEmail(email EmailPayload) error {
	smtpHost := "smtp.gmail.com"
	smtpPort := "587"
	auth := smtp.PlainAuth("", os.Getenv("SMTP_EMAIL"), os.Getenv("SMTP_PASS"), smtpHost)

	attachments := ""
	for _, attachment := range email.Attachments {
		if attachment != "" {
			attachments += "\nAttachment: " + attachment
		}
	}

	msg := []byte("To: " + email.To + "\r\n" +
		"Subject: " + email.Subject + "\r\n" +
		"\r\n" +
		email.Body + attachments + "\r\n")

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

	err = createOrGetStream(js)
	if err != nil {
		log.Fatal(err)
	}

	_, err = js.Subscribe("message.send", func(m *nats.Msg) {
		var email EmailPayload
		if err := json.Unmarshal(m.Data, &email); err != nil {
			log.Printf("Error parsing email payload: %v\n", err)
			return
		}

		var wg sync.WaitGroup
		ch := make(chan string, len(email.Attachments))

		for _, url := range email.Attachments {
			wg.Add(1)
			go downloadFile(url, &wg, ch)
		}

		wg.Wait()
		close(ch)

		var downloadedFiles []string
		for file := range ch {
			if file != "" {
				downloadedFiles = append(downloadedFiles, file)
			}
		}

		email.Attachments = downloadedFiles

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
