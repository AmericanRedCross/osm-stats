var promise = require('bluebird');

// Adding these back because we are using them in the pie chart
exports.up = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.decimal('total_road_count_add', 40, 20).defaultTo(0);
    table.decimal('total_road_count_mod', 40, 20).defaultTo(0);
  })
  .then(function () {
    return knex('changesets').select('id', 'user_id', 'road_count_add', 'road_count_mod')
    .then(function (results) {
      return promise.map(results, function (result) {
        return knex('users')
        .where('id', result.user_id)
        .increment('total_road_count_add', result.road_count_add)
        .then(function () {
          return knex('users')
          .where('id', result.user_id)
          .increment('total_road_count_mod', result.road_count_mod);
        });
      });
    });
  });
};

exports.down = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.dropColumn('total_road_count_mod');
    table.dropColumn('total_road_count_add');
  });
};
