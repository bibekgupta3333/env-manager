class EnvManager < Formula
  desc "Cross-language virtual environment manager"
  homepage "https://github.com/bibekgupta3333/env-manager"
  url "https://github.com/bibekgupta3333/env-manager/releases/download/v0.1.0/envs-macos.tar.gz"
  version "0.1.0"
  sha256 "PLACEHOLDER"  # Replace with: shasum -a 256 envs-macos.tar.gz

  def install
    bin.install "envs"
  end

  test do
    system "#{bin}/envs", "--help"
  end
end
