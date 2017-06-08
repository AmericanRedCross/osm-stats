FROM node:4.2

ENV API_VERSION v0.5.0

RUN curl -sSL https://github.com/AmericanRedCross/osm-stats-api/archive/${API_VERSION}.tar.gz \
  | tar -v -C /usr/src -xz

WORKDIR /usr/src/osm-stats-api-${API_VERSION}
RUN npm install

CMD ["npm", "start"]
