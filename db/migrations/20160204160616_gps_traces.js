exports.up = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.dropColumn('total_gpstrace_km_add');
    table.decimal('total_gps_trace_count_add', 40, 20);
    table.timestamp('total_gps_trace_updated_from_osm');
  });
};

exports.down = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.decimal('total_gpstrace_km_add');
    table.dropColumn('total_gps_trace_count_add');
    table.dropColumn('total_gps_trace_updated_from_osm');
  });
};
