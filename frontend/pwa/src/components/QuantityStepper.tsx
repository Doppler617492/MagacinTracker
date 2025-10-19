/**
 * Manhattan-style Large Quantity Stepper
 * Design: Active WMS clarity-first with large tap targets
 * Optimized for Zebra TC21/MC3300 touch screens
 */

import React, { useState, useEffect } from 'react';
import { Button, InputNumber, Space, Typography } from 'antd';
import { MinusOutlined, PlusOutlined } from '@ant-design/icons';
import './QuantityStepper.css';

const { Text } = Typography;

interface QuantityStepperProps {
  min?: number;
  max: number;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
  label?: string;
  unit?: string;
}

export const QuantityStepper: React.FC<QuantityStepperProps> = ({
  min = 0,
  max,
  value,
  onChange,
  disabled = false,
  label,
  unit = 'kom',
}) => {
  const [inputValue, setInputValue] = useState(value);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  const handleIncrement = () => {
    const newValue = Math.min(inputValue + 1, max);
    setInputValue(newValue);
    onChange(newValue);
  };

  const handleDecrement = () => {
    const newValue = Math.max(inputValue - 1, min);
    setInputValue(newValue);
    onChange(newValue);
  };

  const handleInputChange = (val: number | null) => {
    if (val === null) return;
    
    const newValue = Math.min(Math.max(val, min), max);
    setInputValue(newValue);
    onChange(newValue);
  };

  const canDecrement = inputValue > min && !disabled;
  const canIncrement = inputValue < max && !disabled;

  return (
    <div className="quantity-stepper">
      {label && (
        <div className="quantity-stepper__label">
          <Text strong>{label}</Text>
        </div>
      )}
      
      <div className="quantity-stepper__controls">
        {/* Decrement Button */}
        <Button
          type="default"
          size="large"
          icon={<MinusOutlined />}
          onClick={handleDecrement}
          disabled={!canDecrement}
          className="quantity-stepper__button quantity-stepper__button--minus"
          aria-label="Smanji količinu"
        />

        {/* Input Field */}
        <div className="quantity-stepper__input-wrapper">
          <InputNumber
            min={min}
            max={max}
            value={inputValue}
            onChange={handleInputChange}
            disabled={disabled}
            className="quantity-stepper__input"
            controls={false}
            keyboard
            aria-label="Unesi količinu"
          />
          {unit && (
            <Text className="quantity-stepper__unit" type="secondary">
              {unit}
            </Text>
          )}
        </div>

        {/* Increment Button */}
        <Button
          type="default"
          size="large"
          icon={<PlusOutlined />}
          onClick={handleIncrement}
          disabled={!canIncrement}
          className="quantity-stepper__button quantity-stepper__button--plus"
          aria-label="Povećaj količinu"
        />
      </div>

      {/* Max Label */}
      <div className="quantity-stepper__max">
        <Text type="secondary" className="quantity-stepper__max-text">
          Maksimalno: {max} {unit}
        </Text>
      </div>
    </div>
  );
};

export default QuantityStepper;

