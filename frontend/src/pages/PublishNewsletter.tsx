import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  Input,
  InputGroup,
  InputLeftElement,
  InputRightAddon,
  Icon,
  useToast,
} from '@chakra-ui/react';
import { ArrowLeftIcon } from '../assets/icons/ArrowLeftIcon';
import { Stepper } from '../components/organisms/Stepper';
import { Card } from '../components/atoms/Card';
import { apiService } from '../services/apiService';

const STEPS = [
  { number: 1, label: 'Create' },
  { number: 2, label: 'Review' },
  { number: 3, label: 'Publish' },
];

const MailIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path
      d="M2.66663 5.33333L7.99996 8.66667L13.3333 5.33333M2.66663 4H13.3333C13.7015 4 14 4.29848 14 4.66667V11.3333C14 11.7015 13.7015 12 13.3333 12H2.66663C2.29844 12 1.99996 11.7015 1.99996 11.3333V4.66667C1.99996 4.29848 2.29844 4 2.66663 4Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const PublishNewsletter = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const newsletterData = location.state;

  const [emails, setEmails] = useState(['', '', '', '', '']);
  const [isPublishing, setIsPublishing] = useState(false);

  const handleEmailChange = (index: number, value: string) => {
    const newEmails = [...emails];
    newEmails[index] = value;
    setEmails(newEmails);
  };

  const handleBack = () => {
    navigate('/review', { state: newsletterData });
  };

  const handlePublish = async () => {
    const validEmails = emails.filter((email) => email.trim());

    if (validEmails.length === 0) {
      toast({
        title: 'Adicione pelo menos um email',
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
            <Stepper steps={STEPS} currentStep={3} />
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
                Publish
              </Heading>
              <Text fontSize="18px" fontWeight="normal" color="#111111" lineHeight="28px">
                Set your audience and send your newsletter to the world.
              </Text>
            </VStack>
          </Box>

          <Box flex={1} maxW="752px">
            <VStack spacing={4} align="stretch">
              <Card>
                <VStack spacing={5} align="stretch">
                  <Heading
                    as="h3"
                    fontSize="16px"
                    fontWeight="semibold"
                    color="#111111"
                    lineHeight="24px"
                  >
                    Mailing publishing list
                  </Heading>

                  {emails.map((email, index) => (
                    <VStack key={index} spacing={1.5} align="start">
                      <Text fontSize="14px" fontWeight="semibold" color="black">
                        Email
                      </Text>
                      <InputGroup size="md">
                        <InputLeftElement pointerEvents="none" opacity={0.7}>
                          <Icon as={MailIcon} color="gray.700" />
                        </InputLeftElement>
                        <Input
                          value={email}
                          onChange={(e) => handleEmailChange(index, e.target.value)}
                          placeholder="example@chakraui"
                          fontSize="14px"
                          borderColor="gray.200"
                          _focus={{ borderColor: 'gray.900' }}
                        />
                        <InputRightAddon fontSize="14px" bg="white" borderColor="gray.200">
                          .com
                        </InputRightAddon>
                      </InputGroup>
                    </VStack>
                  ))}
                </VStack>
              </Card>

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
                  Back: review
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
