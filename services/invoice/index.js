const { connect, StringCodec, AckPolicy } = require('nats');
const puppeteer = require('puppeteer');
const Minio = require('minio');
const fs = require('fs');
const path = require('path');
const Handlebars = require('handlebars');
require('dotenv').config();

const sc = StringCodec();


const minioClient = new Minio.Client({
    endPoint: 'localhost',
    port: 9000,
    useSSL: false,
    accessKey: 'minio',
    secretKey: 'miniopass'
});


const ensureBucketExists = async (bucketName) => {
    try {
        const exists = await minioClient.bucketExists(bucketName);
        if (!exists) {
            await minioClient.makeBucket(bucketName, 'us-east-1');
        }
    } catch (err) {
        console.error('Error ensuring bucket exists:', err);
    }
};

const uploadToMinio = async (filePath, fileName) => {
    const bucketName = 'invoices';
    await ensureBucketExists(bucketName);
    return new Promise((resolve, reject) => {
        minioClient.fPutObject(bucketName, fileName, filePath, (err, etag) => {
            if (err) return reject(err);
            resolve(etag);
        });
    });
};

const getPresignedUrl = async (fileName) => {
    try {
        return await minioClient.presignedGetObject('invoices', fileName, 24 * 60 * 60);
    } catch (err) {
        console.error('Error generating presigned URL:', err);
        throw err;
    }
};

const generateInvoice = async (orderData) => {
    const currentDate = new Date().toLocaleDateString();
    const invoiceData = {
        order_id: orderData.order_id,
        order_date: currentDate,
        customer_name: 'John Doe',
        payment_method: 'Credit Card',
        total_amount: '$1000',
        items: [
            { item_name: 'Product A', item_qty: 2, item_price: '$500', item_total: '$1000' },
        ],
        current_year: new Date().getFullYear(),
    };

    let invoiceHtml = fs.readFileSync(path.join(__dirname, 'invoice-template.html'), 'utf8');
    const template = Handlebars.compile(invoiceHtml);
    const compiledHtml = template(invoiceData);

    const browser = await puppeteer.launch({
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    const page = await browser.newPage();
    await page.setContent(compiledHtml);
    const pdfPath = path.join(__dirname, `invoice-${orderData.order_id}.pdf`);
    await page.pdf({ path: pdfPath, format: 'A4' });
    await browser.close();

    const fileName = `invoice-${orderData.order_id}.pdf`;
    await uploadToMinio(pdfPath, fileName);
    fs.unlinkSync(pdfPath);

    return fileName;
};

const startConsumer = async () => {
    try {
       
        const nats_url = process.env.NATS_URL || 'localhost:30042'
        const nc = await connect({ servers: nats_url });
        console.log('Connected to NATS');

        
        const js = nc.jetstream();

        const jsm = await nc.jetstreamManager();
        const ci = await jsm.consumers.add("events", {
          name: "complete-event-consumer",
          ack_policy: AckPolicy.Explicit,
          filter_subject: "events.complete"
        });

        const consumer = await js.consumers.get("events", ci.name); 

        console.log('Consumer created, waiting for messages...');

        
        const processMessages = async () => {
            try {
                for await (const msg of await consumer.consume()) {
                    try {
                        const data = JSON.parse(sc.decode(msg.data));
                        console.log('Received order:', data.order_id);
                        const fileName = await generateInvoice(data);
                        const presignedUrl = await getPresignedUrl(fileName);
                        await js.publish('message.send', sc.encode(JSON.stringify({
                            to: data.email,
                            subject: "Invoice",
                            body: `Hey, your order id: ${data.order_id} has been processed successfully`,
                            attachments: [presignedUrl],
                        })));
                        await msg.ack();
                        console.log('Successfully processed invoice for order:', data.order_id);
                    } catch (error) {
                        console.error('Error processing message:', error);
                        
                        await msg.nak();
                    }
                }
            } catch (error) {
                console.error('Error in message processing:', error);
                
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            
            processMessages();
        };

        
        processMessages();

    } catch (error) {
        console.error('Error starting consumer:', error);
        process.exit(1);
    }
};


startConsumer().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
