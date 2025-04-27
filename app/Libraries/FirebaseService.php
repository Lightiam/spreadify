<?php

namespace App\Libraries;

use Config\Firebase as FirebaseConfig;
use Kreait\Firebase\Factory;
use Kreait\Firebase\ServiceAccount;

class FirebaseService
{
    protected $firebase;
    protected $database;
    protected $storage;
    protected $auth;

    public function __construct()
    {
        $config = new FirebaseConfig();
        
        $factory = (new Factory)
            ->withServiceAccount($config->serviceAccountKeyFile)
            ->withDatabaseUri($config->databaseUrl);
            
        $this->firebase = $factory->createFirebase();
        $this->database = $factory->createDatabase();
        $this->storage = $factory->createStorage();
        $this->auth = $factory->createAuth();
    }

    /**
     * Get Firebase Database
     *
     * @return \Kreait\Firebase\Database
     */
    public function getDatabase()
    {
        return $this->database;
    }

    /**
     * Get Firebase Storage
     *
     * @return \Kreait\Firebase\Storage
     */
    public function getStorage()
    {
        return $this->storage;
    }

    /**
     * Get Firebase Auth
     *
     * @return \Kreait\Firebase\Auth
     */
    public function getAuth()
    {
        return $this->auth;
    }
}
