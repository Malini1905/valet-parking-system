from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from ticketingapp.models import Mall, ParkingTicket, Tenant

# Create your tests here.


class MallViewSet(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.mall = Mall.objects.create(name='Marryland')

    def test_can_create_mall(self):
        url = reverse('mall-list')
        response = self.client.post(url, data={'name': 'ICM'})

        # assert status code for created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert data returned contains mall
        self.assertEqual(response.data['name'], 'ICM')

    def test_can_get_mall(self):
        url = reverse('mall-detail', kwargs={'pk': self.mall.id})
        response = self.client.get(url)

        # test mall returned
        self.assertEqual(response.data['name'], self.mall.name)

    def test_can_edit_mall(self):
        url = reverse('mall-detail', kwargs={'pk': self.mall.id})
        response = self.client.put(url, kwargs={'name': 'Ikeja City Mall'})

        self.assertEqual(response.data['name'], self.mall.name)

    def test_can_delete(self):
        url = reverse('mall-detail', kwargs={'pk': self.mall.id})
        mall_id = self.mall.id

        response = self.client.delete(url)

        # assert mall delete response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert model deleted
        with self.assertRaises(Mall.DoesNotExist):
            Mall.objects.get(pk=mall_id)

    def test_payment(self):
        url = reverse('payment-details-route',
                      kwargs={'mall_id': self.mall.id})
        parkingticket = ParkingTicket.objects.create(
            plate_number="ZYX-984SD",
            mall=self.mall
        )

        parkingticket.entry_time = \
            timezone.make_aware(
                datetime.now() - timedelta(hours=2, minutes=50))

        parkingticket.save()

        ticket_fee = parkingticket.checkout()

        # assert amount owned
        response = self.client.get(url)
        self.assertEqual(response.data['owned'], ticket_fee)
        self.assertEqual(response.data['paid'], 0)

        payment_url = reverse(
            'payment-route', kwargs={'ticket_id': parkingticket.id})

        payment_response = self.client.post(
            payment_url, data={'fee_paid': ticket_fee})

        # assert payment made
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)

        second_response = self.client.get(url)

        # assert amount paid
        self.assertEqual(second_response.data['owned'], 0)
        self.assertEqual(second_response.data['paid'], ticket_fee)


class ParkingTicketTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.mall = Mall.objects.create(name='ICM')
        self.parkingticket = ParkingTicket.objects.create(
            plate_number="ZYX-984SD",
            mall=self.mall
        )

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

    def test_can_edit(self):
        url = reverse('parkingticket-detail',
                      kwargs={'pk': self.parkingticket.id})
        new_plate_number = 'ZXY-111DF'
        response = self.client.put(
            url, data={'plate_number': new_plate_number})

        # assert successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert editted response
        self.assertEqual(response.data['plate_number'], new_plate_number)

    def test_delete_edit(self):
        url = reverse('parkingticket-detail',
                      kwargs={'pk': self.parkingticket.id})

        response = self.client.delete(url)

        # assert response code
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert model deleted
        with self.assertRaises(ParkingTicket.DoesNotExist):
            ParkingTicket.objects.get(pk=self.parkingticket.id)

    def test_park_exit(self):
        url = reverse(
            'exit-route', kwargs={'ticket_id': self.parkingticket.id})

        self.parkingticket.entry_time = \
            timezone.make_aware(
                datetime.now() - timedelta(hours=2, minutes=50))

        self.parkingticket.save()

        response = self.client.get(url)

        # assert can't exit with outstandind fee
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        ticket_fee = self.parkingticket.checkout()
        self.parkingticket.pay_ticket(ticket_fee)

        # assert can exit when fee is paid
        second_response = self.client.get(url)

        self.assertEqual(second_response.status_code, status.HTTP_200_OK)


class TenantTent(APITestCase):

    def setUp(self):
        self.mall = Mall.objects.create(name='Marryland')
        self.tenant = Tenant.objects.create(
            name='KFC'
        )
        self.tenant.malls.set([self.mall])
        self.parkingticket = ParkingTicket.objects.create(
            plate_number="ZYX-984SD",
            mall=self.mall,
            tenant=self.tenant
        )

    def test_tenant_fee_parking(self):
        self.parkingticket.entry_time = \
            timezone.make_aware(
                datetime.now() - timedelta(hours=2, minutes=50))

        self.parkingticket.save()

        url = reverse('parkingticket-detail',
                      kwargs={'pk': self.parkingticket.id})
        response = self.client.get(url)

        # assert no amount owned
        self.assertEqual(response.data['ticket_fee'], 0)

    def test_tenant_create(self):
        url = reverse('tenant-list')
        mall_url = reverse('mall-detail', kwargs={'pk': self.mall.id})
        data = {
            'name': 'Adidas',
            'malls': [mall_url],
        }
        response = self.client.post(url, data=data)

        # assert successly created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert response data contains name
        self.assertEqual(response.data['name'], data['name'])

    def test_can_edit(self):
        url = reverse('tenant-detail', kwargs={'pk': self.tenant.id})
        new_name = 'Fifa'
        response = self.client.put(url, data={'name': new_name})

        # assert successful status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert name changed
        self.assertEqual(response.data['name'], new_name)

    def test_can_delete(self):
        url = reverse('tenant-detail', kwargs={'pk': self.tenant.id})

        response = self.client.delete(url)

        # assert successful
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert model deleted
        with self.assertRaises(Tenant.DoesNotExist):
            Tenant.objects.get(pk=self.tenant.id)
