<?php

namespace App\Models;

class PurchasesModel extends FirebaseModel
{
    protected $collection = 'purchases';
    
    /**
     * Find purchases by item ID
     *
     * @param string $itemId
     * @return array
     */
    public function findByItemId($itemId)
    {
        $snapshot = $this->getReference()->orderByChild('item_id')->equalTo($itemId)->getSnapshot();
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
     * Find main purchase
     *
     * @return array|null
     */
    public function findMainPurchase()
    {
        $snapshot = $this->getReference()->orderByChild('is_main')->equalTo(true)->getSnapshot();
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
