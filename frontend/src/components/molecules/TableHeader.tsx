import { Th } from '@chakra-ui/react';

interface TableHeaderProps {
  children: React.ReactNode;
  width?: string;
}

export const TableHeader = ({ children, width }: TableHeaderProps) => {
  return (
    <Th
      fontSize="14px"
      fontWeight="semibold"
      color="black"
      borderBottom="1px solid"
      borderColor="gray.200"
      py="12px"
      px="12px"
      textTransform="none"
      letterSpacing="normal"
      width={width}
    >
      {children}
    </Th>
  );
};
