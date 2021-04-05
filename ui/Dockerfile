# Use the official image as a parent image
FROM node:12

# Set the working directory
WORKDIR /app

# RUN mkdir -p /opt
# ADD latest.tar.gz /opt/
# RUN mv /opt/dist /opt/yarn
# ENV PATH "$PATH:/opt/yarn/bin"

# Copy the file from your host to your current location
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build
RUN yarn global add serve

# Run the specified command within the container.
CMD [ "serve", "-s",  "build" ]
