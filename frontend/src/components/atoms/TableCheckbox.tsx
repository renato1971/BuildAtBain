import { Checkbox } from '@chakra-ui/react';

interface TableCheckboxProps {
  isChecked?: boolean;
  onChange?: (checked: boolean) => void;
}

export const TableCheckbox = ({ isChecked, onChange }: TableCheckboxProps) => {
  return (
    <Checkbox
      isChecked={isChecked}
      onChange={(e) => onChange?.(e.target.checked)}
      size="md"
      colorScheme="gray"
      borderColor="gray.300"
    />
  );
};
