<?php

namespace App\Models;

class UsersModel extends FirebaseModel
{
    protected $collection = 'users';
    
    /**
     * Find user by email
     *
     * @param string $email
     * @return array|null
     */
    public function findByEmail($email)
    {
        $snapshot = $this->getReference()->orderByChild('email')->equalTo($email)->getSnapshot();
        $value = $snapshot->getValue();
        
        if (!empty($value)) {
            $key = array_key_first($value);
            $data = $value[$key];
            $data['id'] = $key;
            return $data;
        }
        
        return null;
    }
    
    /**
     * Find user by username
     *
     * @param string $username
     * @return array|null
     */
    public function findByUsername($username)
    {
        $snapshot = $this->getReference()->orderByChild('username')->equalTo($username)->getSnapshot();
        $value = $snapshot->getValue();
        
        if (!empty($value)) {
            $key = array_key_first($value);
            $data = $value[$key];
            $data['id'] = $key;
            return $data;
        }
        
        return null;
    }
    
    /**
     * Authenticate user
     *
     * @param string $username
     * @param string $password
     * @return array|null
     */
    public function authenticate($username, $password)
    {
        $user = $this->findByUsername($username);
        
        if ($user && password_verify($password, $user['password'])) {
            return $user;
        }
        
        return null;
    }
}
