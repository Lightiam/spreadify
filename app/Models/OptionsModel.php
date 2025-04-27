<?php

namespace App\Models;

class OptionsModel extends FirebaseModel
{
    protected $collection = 'options';
    
    /**
     * Get option value by name
     *
     * @param string $name
     * @return mixed|null
     */
    public function getOption($name)
    {
        $snapshot = $this->getReference()->orderByChild('name')->equalTo($name)->getSnapshot();
        $value = $snapshot->getValue();
        
        if (!empty($value)) {
            $key = array_key_first($value);
            return $value[$key]['value'];
        }
        
        return null;
    }
    
    /**
     * Set option value
     *
     * @param string $name
     * @param mixed $value
     * @return bool
     */
    public function setOption($name, $value)
    {
        $snapshot = $this->getReference()->orderByChild('name')->equalTo($name)->getSnapshot();
        $existingValue = $snapshot->getValue();
        
        if (!empty($existingValue)) {
            $key = array_key_first($existingValue);
            return $this->update($key, ['value' => $value]);
        } else {
            $this->insert([
                'name' => $name,
                'value' => $value
            ]);
            return true;
        }
    }
}
