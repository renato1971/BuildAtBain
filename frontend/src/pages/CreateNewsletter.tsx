import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, Flex, Heading, Text, VStack, Container } from '@chakra-ui/react';
import { ArrowLeftIcon } from '../assets/icons/ArrowLeftIcon';
import { Stepper } from '../components/organisms/Stepper';
import { CreateNewsletterForm } from '../components/organisms/CreateNewsletterForm';
import type { NewsletterFormData } from '../types/newsletterForm';
import { UploadFileSection } from '../components/organisms/UploadFileSection';
import { newsletterStorage } from '../services/newsletterStorage';

const STEPS = [
  { number: 1, label: 'Create' },
  { number: 2, label: 'Review' },
  { number: 3, label: 'Publish' },
];

export const CreateNewsletter = () => {
  const navigate = useNavigate();
  const [currentStep] = useState(1);

  const handleBack = () => {
    navigate('/');
  };

  const handleCancel = () => {
    // Limpar dados ao cancelar
    newsletterStorage.clear();
    navigate('/');
  };

  const handleNext = (data: NewsletterFormData) => {
    navigate('/review', { state: data });
  };

  const handleFileSelect = (files: File[]) => {
    console.log('Files selected:', files);
  };

  return (
    <Box bg="white" minH="100vh" py={8}>
      <Container maxW="1536px" px={8}>
        <Flex mb={8} gap="322px" alignItems="center">
          <Button
            onClick={handleBack}
            variant="ghost"
            leftIcon={<ArrowLeftIcon />}
            fontWeight="semibold"
            fontSize="14px"
            color="gray.800"
            height="36px"
            px={3}
            _hover={{ bg: 'gray.50' }}
          >
            Back
          </Button>

          <Box width="752px">
            <Stepper steps={STEPS} currentStep={currentStep} />
          </Box>
        </Flex>

        <Flex gap={8}>
          <Box width="360px" marginLeft="16px">
            <VStack spacing="48px" align="start">
              <VStack spacing={2} align="start">
                <Heading
                  as="h1"
                  fontSize="36px"
                  fontWeight="semibold"
                  color="#111111"
                  lineHeight="44px"
                >
                  Create newsletter
                </Heading>
                <Text fontSize="18px" fontWeight="normal" color="#111111" lineHeight="28px">
                  Describe your newsletter and we'll get a html template ready for you to review.
                </Text>
              </VStack>

              {/* <DatabaseSection onFileSelect={handleFileSelect} /> */}
              <UploadFileSection name='Tabela' />
              <UploadFileSection name='PDF' />
            </VStack>
          </Box>

          <Box flex={1} maxW="752px">
            <CreateNewsletterForm onCancel={handleCancel} onNext={handleNext} />
          </Box>
        </Flex>
      </Container>
    </Box>
  );
};
