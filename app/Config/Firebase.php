<?php

namespace Config;

use CodeIgniter\Config\BaseConfig;

class Firebase extends BaseConfig
{
    /**
     * Firebase Service Account Key File Path
     *
     * @var string
     */
    public $serviceAccountKeyFile;

    /**
     * Firebase Database URL
     *
     * @var string
     */
    public $databaseUrl;

    /**
     * Firebase Storage Bucket
     *
     * @var string
     */
    public $storageBucket;

    /**
     * Firebase Project ID
     *
     * @var string
     */
    public $projectId;
    
    public function __construct()
    {
        parent::__construct();
        
        $this->serviceAccountKeyFile = getenv('FIREBASE_CREDENTIALS_PATH') ?: ROOTPATH . 'firebase-credentials.json';
        $this->databaseUrl = getenv('FIREBASE_DATABASE_URL') ?: 'https://lightiam-1061.firebaseio.com';
        $this->storageBucket = getenv('FIREBASE_STORAGE_BUCKET') ?: 'lightiam-1061.appspot.com';
        $this->projectId = getenv('FIREBASE_PROJECT_ID') ?: 'lightiam-1061';
    }
}
