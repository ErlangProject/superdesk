# BUILD
FROM node:lts AS build

# install client
WORKDIR /tmp/client
RUN npm install -g grunt-cli
COPY package.json .
RUN npm install --no-audit --legacy-peer-deps
COPY . .
RUN npx grunt build

# DEPLOY
FROM nginx

# setup the environment
WORKDIR /opt/superdesk/client/dist

# build client
COPY --from=build /tmp/client/dist ./

RUN rm /etc/nginx/conf.d/default.conf
COPY ./docker/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/superdesk_vhost.conf /etc/nginx/sites-enabled/superdesk.conf
COPY ./docker/start.sh /opt/superdesk/start.sh

ENTRYPOINT [ "/opt/superdesk/start.sh" ]
RUN rm /opt/superdesk/client/dist/images/superdesk-logo.svg
RUN curl -o /opt/superdesk/client/dist/images/superdesk-logo.svg https://svgshare.com/i/VkZ.svg
RUN rm /opt/superdesk/client/dist/6494665ba33bdf4948db3814dc336e8d.svg
RUN curl -o /opt/superdesk/client/dist/6494665ba33bdf4948db3814dc336e8d.svg https://svgshare.com/i/VkZ.svg

CMD ["nginx", "-g daemon off;"]