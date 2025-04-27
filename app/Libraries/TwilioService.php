<?php

namespace App\Libraries;

use Twilio\Rest\Client;

class TwilioService
{
    protected $client;
    protected $accountSid;
    protected $authToken;
    protected $fromNumber;

    public function __construct()
    {
        $this->accountSid = getenv('TWILIO_ACCOUNT_SID') ?: '';
        $this->authToken = getenv('TWILIO_AUTH_TOKEN') ?: '';
        $this->fromNumber = getenv('TWILIO_FROM_NUMBER') ?: '';
        
        $this->client = new Client($this->accountSid, $this->authToken);
    }

    /**
     * Send SMS message
     *
     * @param string $to Recipient phone number
     * @param string $message Message content
     * @return \Twilio\Rest\Api\V2010\Account\MessageInstance
     */
    public function sendSMS($to, $message)
    {
        return $this->client->messages->create(
            $to,
            [
                'from' => $this->fromNumber,
                'body' => $message
            ]
        );
    }

    /**
     * Get Twilio Client
     *
     * @return \Twilio\Rest\Client
     */
    public function getClient()
    {
        return $this->client;
    }
}
