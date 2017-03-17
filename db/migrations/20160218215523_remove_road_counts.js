exports.up = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.dropColumn('total_road_count_mod');
    table.dropColumn('total_road_count_add');
  });
};

exports.down = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.decimal('total_road_count_add', 40, 20);
    table.decimal('total_road_count_mod', 40, 20);

    // TODO
    // Fill back database from changesets table
  });
};
