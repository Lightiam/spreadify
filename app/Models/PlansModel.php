<?php

namespace App\Models;

class PlansModel extends FirebaseModel
{
    protected $collection = 'plans';
    
    /**
     * Find active plans
     *
     * @return array
     */
    public function findActivePlans()
    {
        $snapshot = $this->getReference()->orderByChild('status')->equalTo(true)->getSnapshot();
        $value = $snapshot->getValue();
        $result = [];
        
        if (!empty($value)) {
            foreach ($value as $key => $data) {
                $data['id'] = $key;
                $result[] = $data;
            }
        }
        
        return $result;
    }
    
    /**
     * Find plan by name
     *
     * @param string $name
     * @return array|null
     */
    public function findByName($name)
    {
        $snapshot = $this->getReference()->orderByChild('name')->equalTo($name)->getSnapshot();
        $value = $snapshot->getValue();
        
        if (!empty($value)) {
            $key = array_key_first($value);
            $data = $value[$key];
            $data['id'] = $key;
            return $data;
        }
        
        return null;
    }
}
