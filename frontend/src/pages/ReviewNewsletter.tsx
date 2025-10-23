import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { ArrowLeftIcon } from '../assets/icons/ArrowLeftIcon';
import { Stepper } from '../components/organisms/Stepper';
import type { NewsletterFormData } from '../types/newsletterForm';
import { useState } from 'react';
import { apiService } from '../services/apiService';
import { newsletterStorage } from '../services/newsletterStorage';

const STEPS = [
  { number: 1, label: 'Create' },
  { number: 2, label: 'Review' },
  { number: 3, label: 'Publish' },
];

export const ReviewNewsletter = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const newsletterData = location.state as (NewsletterFormData & { html?: string; topic?: string }) | undefined;

  const htmlContent = newsletterData?.html ?? '';
  const [title] = useState('Preview HTML Newsletter');
  const [isPublishing, setIsPublishing] = useState(false);

  const handleBack = () => {
    navigate('/create', { state: newsletterData });
  };

  const handlePublish = async () => {
    if (!newsletterData?.topic || !newsletterData?.html) {
      toast({
        title: 'Dados incompletos',
        description: 'Topic e HTML são necessários para publicar a newsletter',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsPublishing(true);

    try {
      const savedNewsletter = await apiService.createNewsletter(
        newsletterData.topic,
        newsletterData.html
      );

      // Limpar dados após publicar com sucesso
      newsletterStorage.clear();

      toast({
        title: 'Newsletter publicada com sucesso!',
        description: `Newsletter salva com ID: ${savedNewsletter.id}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      navigate('/');
    } catch (error) {
      toast({
        title: 'Erro ao publicar newsletter',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsPublishing(false);
    }
  };

  if (!newsletterData) {
    navigate('/create');
    return null;
  }

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
            <Stepper steps={STEPS} currentStep={2} />
          </Box>
        </Flex>

        <Flex gap={8}>
          <Box width="360px" marginLeft="16px">
            <VStack spacing={2} align="start">
              <Heading
                as="h1"
                fontSize="36px"
                fontWeight="semibold"
                color="#111111"
                lineHeight="44px"
              >
                Review
              </Heading>
              <Text fontSize="18px" fontWeight="normal" color="#111111" lineHeight="28px">
                Ensure accuracy, relevance, and appeal before publishing.
              </Text>
            </VStack>
          </Box>

          <Box flex={1} maxW="752px">
            <VStack spacing={4} align="stretch">
              <Box
                bg="white"
                p={4}
                borderRadius="6px"
                boxShadow="0px 0px 1px 0px rgba(24, 24, 27, 0.3), 0px 4px 8px 0px rgba(24, 24, 27, 0.1)"
              >
                <VStack spacing={4} align="stretch">
                  <Heading
                    as="h3"
                    fontSize="16px"
                    fontWeight="semibold"
                    color="#111111"
                    lineHeight="24px"
                  >
                    {title}
                  </Heading>

                  <Box
                    border="1px solid"
                    borderColor="gray.200"
                    borderRadius="6px"
                    p={4}
                    fontSize="14px"
                    lineHeight="22px"
                    minH="200px"
                    // Sanitize before using in production (e.g., DOMPurify)
                    dangerouslySetInnerHTML={{
                      __html: htmlContent || '<p style="color:#666;">No HTML content provided.</p>',
                    }}
                  />
                </VStack>
              </Box>

              <Flex gap={2} justifyContent="flex-end">
                <Button
                  onClick={handleBack}
                  variant="outline"
                  borderColor="gray.200"
                  color="gray.800"
                  fontWeight="semibold"
                  fontSize="14px"
                  height="40px"
                  _hover={{ bg: 'gray.50' }}
                >
                  Back: edit
                </Button>
                <Button
                  onClick={handlePublish}
                  bg="gray.900"
                  color="white"
                  fontWeight="semibold"
                  fontSize="14px"
                  height="40px"
                  _hover={{ bg: 'gray.800' }}
                  isLoading={isPublishing}
                >
                  Publish newsletter
                </Button>
              </Flex>
            </VStack>
          </Box>
        </Flex>
      </Container>
    </Box>
  );
};