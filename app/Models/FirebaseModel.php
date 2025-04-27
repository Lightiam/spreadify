<?php

namespace App\Models;

use App\Libraries\FirebaseService;

abstract class FirebaseModel
{
    protected $firebaseService;
    protected $database;
    protected $collection;

    public function __construct()
    {
        $this->firebaseService = new FirebaseService();
        $this->database = $this->firebaseService->getDatabase();
    }

    /**
     * Get reference to the collection
     *
     * @return \Kreait\Firebase\Database\Reference
     */
    protected function getReference()
    {
        return $this->database->getReference($this->collection);
    }

    /**
     * Find a record by ID
     *
     * @param string $id
     * @return array|null
     */
    public function find($id)
    {
        $snapshot = $this->getReference()->getChild($id)->getSnapshot();
        
        if ($snapshot->exists()) {
            $data = $snapshot->getValue();
            $data['id'] = $snapshot->getKey();
            return $data;
        }
        
        return null;
    }

    /**
     * Find all records
     *
     * @return array
     */
    public function findAll()
    {
        $snapshot = $this->getReference()->getSnapshot();
        $result = [];
        
        foreach ($snapshot->getValue() as $key => $value) {
            $value['id'] = $key;
            $result[] = $value;
        }
        
        return $result;
    }

    /**
     * Insert a new record
     *
     * @param array $data
     * @return string The ID of the new record
     */
    public function insert($data)
    {
        $data['created_at'] = date('Y-m-d H:i:s');
        $data['updated_at'] = date('Y-m-d H:i:s');
        
        $newRef = $this->getReference()->push($data);
        return $newRef->getKey();
    }

    /**
     * Update a record
     *
     * @param string $id
     * @param array $data
     * @return bool
     */
    public function update($id, $data)
    {
        $data['updated_at'] = date('Y-m-d H:i:s');
        
        $this->getReference()->getChild($id)->update($data);
        return true;
    }

    /**
     * Delete a record
     *
     * @param string $id
     * @return bool
     */
    public function delete($id)
    {
        $this->getReference()->getChild($id)->remove();
        return true;
    }
}
