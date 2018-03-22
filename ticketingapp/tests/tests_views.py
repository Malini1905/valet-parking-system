from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from ticketingapp.models import Mall

# Create your tests here.


class MallViewSetTest(APITestCase):

    def test_mall_create(self):
        client = APIClient()
        url = reverse('mall-list')
        response = client.post(url, data={'name': 'ICM'})

        # assert status code for created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert data returned contains mall
        self.assertEqual(response.data['name'], 'ICM')


class ParkingTicketViewSetTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.mall = Mall.objects.create(name='ICM')

    def test_parking_ticket_create(self):
        url = reverse('parkingticket-list')
        data = {
            'plate_number': 'ABC-123DE',
            'mall': self.mall.id
        }
        response = self.client.post(url, data=data)
        
        # assert status code for created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert response contains data
        self.assertEqual(response.data['plate_number'], data['plate_number'])

    def test_plate_number_validation(self):
        url = reverse('parkingticket-list')
        data = {
            'plate_number': 'invalid-platenumber1223',
            'mall': self.mall.id
        }

        response = self.client.post(url, data=data)

        # assert error status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert error message
        self.assertIn("Plate Number are in the format ABC-123DE",
                      str(response.content))  # cast byte object to string