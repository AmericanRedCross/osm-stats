exports.up = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.dropColumn('avatar');
    table.dropColumn('total_gpstrace_count_add');
    table.decimal('total_tm_done_count', 40, 20);
    table.decimal('total_tm_val_count', 40, 20);
    table.decimal('total_tm_inval_count', 40, 20);
  });
};

exports.down = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.dropColumn('total_tm_inval_count');
    table.dropColumn('total_tm_val_count');
    table.dropColumn('total_tm_done_count');
    table.decimal('total_gpstrace_count_add', 40, 20);
    table.string('avatar');
  });
};
