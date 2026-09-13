const kFeaturedPujaNames = [
  'Satyanarayan Puja',
  'Griha Pravesh',
  'Navagraha Shanti',
  'Rudrabhishek',
];

const kCategoryOrder = [
  'Household Pujas',
  'Life Events',
  'Weddings',
  'Festivals',
  'Deity Pujas',
  'Planetary Shanti',
  'Ancestral Rites',
  'Special Rituals',
];

int catalogCategoryRank(String name) {
  final index = kCategoryOrder.indexOf(name);
  return index < 0 ? kCategoryOrder.length : index;
}

List<T> sortByCatalogCategory<T>(List<T> items, String Function(T) nameOf) {
  final copy = List<T>.from(items);
  copy.sort((a, b) {
    final rank = catalogCategoryRank(nameOf(a)).compareTo(catalogCategoryRank(nameOf(b)));
    if (rank != 0) return rank;
    return nameOf(a).compareTo(nameOf(b));
  });
  return copy;
}
