import 'package:flutter_test/flutter_test.dart';
import 'package:purohit_mobile/core/models/models.dart';
import 'package:purohit_mobile/core/state/booking_provider.dart';

PurohitModel _purohit({required CoverageInfo coverage}) {
  return PurohitModel.fromJson({
    'id': 1,
    'name': 'Pt Test',
    'slug': 'pt-test',
    'city': 'Hyderabad',
    'base_price': 2100,
    'coverage': {
      'acceptsTravel': coverage.acceptsTravel,
      'permanent': coverage.permanent
          .map((place) => {
                'city_id': place.cityId,
                'area_id': place.areaId,
                'kind': place.kind,
              })
          .toList(),
      'places': coverage.places
          .map((place) => {
                'city_id': place.cityId,
                'area_id': place.areaId,
                'kind': place.kind,
                'start': place.start,
                'end': place.end,
                'label': place.label,
              })
          .toList(),
    },
  });
}

void main() {
  late BookingProvider booking;
  final hyderabad = CityModel(id: 3, name: 'Hyderabad', state: 'Telangana', areas: [
    AreaModel(id: 9, name: 'Jubilee Hills'),
    AreaModel(id: 8, name: 'Banjara Hills'),
  ]);

  setUp(() {
    booking = BookingProvider();
  });

  test('purohit-place venue is always covered', () {
    booking.setVenueType('purohit');
    expect(booking.coverageStatus.mode, CoverageMode.covered);
  });

  test('permanent offer covers that city and area', () {
    booking.selectPurohit(_purohit(
      coverage: CoverageInfo(
        acceptsTravel: true,
        permanent: [CoveragePlace(cityId: 3, areaId: 9, kind: 'permanent')],
      ),
    ));
    booking.setCity(hyderabad);
    booking.setArea(hyderabad.areas.first);
    expect(booking.coverageStatus.mode, CoverageMode.covered);
    expect(booking.coverageStatus.title, contains('already offer'));
  });

  test('uncovered place with travel asks first', () {
    booking.selectPurohit(_purohit(
      coverage: CoverageInfo(acceptsTravel: true, permanent: const []),
    ));
    booking.setCity(hyderabad);
    booking.setArea(hyderabad.areas.first);
    expect(booking.coverageStatus.mode, CoverageMode.ask);
    expect(booking.coverageStatus.title, contains('Ask them to visit'));
  });

  test('uncovered place is closed when they do not take travel', () {
    booking.selectPurohit(_purohit(
      coverage: CoverageInfo(acceptsTravel: false, permanent: const []),
    ));
    booking.setCity(hyderabad);
    booking.setArea(hyderabad.areas.first);
    expect(booking.coverageStatus.mode, CoverageMode.closed);
  });

  test('visit window covers a date inside the range', () {
    booking.selectPurohit(_purohit(
      coverage: CoverageInfo(
        acceptsTravel: true,
        places: [
          CoveragePlace(
            cityId: 3,
            areaId: 9,
            kind: 'visit',
            start: '2026-09-20',
            end: '2026-09-22',
            label: 'Jubilee Hills visit',
          ),
        ],
      ),
    ));
    booking.setCity(hyderabad);
    booking.setArea(hyderabad.areas.first);
    booking.setDate(DateTime(2026, 9, 21));
    expect(booking.coverageStatus.mode, CoverageMode.covered);
    expect(booking.coverageStatus.body, contains('Jubilee Hills visit'));
  });
}
